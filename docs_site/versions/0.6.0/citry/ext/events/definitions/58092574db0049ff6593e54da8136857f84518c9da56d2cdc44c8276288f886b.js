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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_hover_card_44054f9b = _resolveComponent("citry-c-hover-card-44054f9b")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("div", null, [
    (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
      open: _ctx.open,
      onOpenChange: (next)=>_ctx.open=next,
      "citry-id": _ctx.$citryPrepared.calls.citryCall0870e4d0f2ecc086.id,
      key: _ctx.$citryPrepared.calls.citryCall0870e4d0f2ecc086.key
    }, {
      ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
        _createElementVNode("a", _mergeProps({ href: "#atlas" }, _ctx.$citryPrepared.citryAttrs0), "Atlas workspace", 16 /* FULL_PROPS */)
      ]),
      ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
        _createElementVNode("strong", null, "Atlas"),
        _createElementVNode("p", null, "12 collaborators · Active now")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      onClick: $event => (_ctx.open=!_ctx.open),
      "citry-id": _ctx.$citryPrepared.calls.citryCallafd7dcacd551b65e.id,
      key: _ctx.$citryPrepared.calls.citryCallafd7dcacd551b65e.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Toggle preview")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3404bc726dacc98a9da7ddd1d7104677454aed7b6af7bd9dc280e29a20e0847c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0870e4d0f2ecc086","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":38,"sourceEnd":50},{"kind":"prop","name":":onOpenChange","value":"(next)=>open=next","sourceStart":51,"sourceEnd":84}],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallafd7dcacd551b65e","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"open=!open","sourceStart":522,"sourceEnd":541}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_hover_card_b7a669de = _resolveComponent("citry-controlled-hover-card-b7a669de")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_hover_card_b7a669de, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld825c46edc59c35e.id,
      key: _ctx.$citryPrepared.calls.citryCalld825c46edc59c35e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c4f68c169de51d7ec46db0a0cd3a5aa592cd23159503d91a0247af6485f9a6ad"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld825c46edc59c35e","typeKey":"ControlledHoverCard_664427","componentTag":"citry-controlled-hover-card-b7a669de","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
