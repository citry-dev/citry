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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        (_ctx.$citryPrepared.selectedSlots['citrySlotec0cc8e04efc4941'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotec0cc8e04efc4941", { key: 0 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("div", {
        class: "cui-sidebar__content",
        "data-citry-ui-part": "content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotd4c23e675a840070'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotd4c23e675a840070", { key: 1 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("footer", {
        class: "cui-sidebar__footer",
        "data-citry-ui-part": "footer"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot7f4372daadeaa945'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot7f4372daadeaa945", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e87eb70033260db116789716af1945945f3e195deaee6010973f8312e7edd199"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    ['citrySlotec0cc8e04efc4941']: _withCtx(() => [
      _createElementVNode("strong", null, "Inspector")
    ]),
    ['citrySlotd4c23e675a840070']: _withCtx(() => [
      _createElementVNode("p", null, "Long tool content scrolls independently between fixed regions."),
      _createElementVNode("p", null, "Keep adding contextual controls here.")
    ]),
    ['citrySlot7f4372daadeaa945']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6c342753b1c6facb.id,
        key: _ctx.$citryPrepared.calls.citryCall6c342753b1c6facb.key
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["29a91f501c6a18ab46e7f29ad8b129ff2e8fc766af57ffdefe8df7ba897dca04"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6c342753b1c6facb","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall714599dc372b65cf","typeKey":"CSidebar_25c49a","componentTag":"citry-c-sidebar-73161829","bindings":[],"fills":[{"name":"citrySlot7f4372daadeaa945","localDescendants":["citryCall6c342753b1c6facb"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd4c23e675a840070","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotec0cc8e04efc4941","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_sidebar_presentation_c2e15ba3 = _resolveComponent("citry-sidebar-presentation-c2e15ba3")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_sidebar_presentation_c2e15ba3, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall76d6e5123738d619.id,
      key: _ctx.$citryPrepared.calls.citryCall76d6e5123738d619.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4743bf3fdf395ba395cc300fcfe2c2c0c9e6fd6927162ed07e52f7656adfbadb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall76d6e5123738d619","typeKey":"SidebarPresentation_bcc80f","componentTag":"citry-sidebar-presentation-c2e15ba3","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
