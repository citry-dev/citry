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
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("section", _mergeProps({
    ref: "root",
    class: "cui-toast-region",
    role: "region",
    tabindex: "-1",
    "data-citry-ui-part": "region"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-toast-region__announcer",
      "aria-live": "polite",
      "aria-atomic": "true",
      "data-citry-ui-part": "announcer-polite"
    }),
    _createElementVNode("div", {
      class: "cui-toast-region__announcer",
      "aria-live": "assertive",
      "aria-atomic": "true",
      "data-citry-ui-part": "announcer-assertive"
    }),
    _createElementVNode("div", {
      class: "cui-toast-region__list",
      "data-citry-toast-list": ""
    })
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4994fa44509aff7581f9b4a5c2e466ebf4d2ce0f6e57a0e5d8dd0b3f2c1841b8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", { class: "toast-example" }, [
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      onClick: $event => (_ctx.notices = [..._ctx.notices, {
    id: `note-${_ctx.next}`, title: `Observation ${_ctx.next++} queued`, intent: 'info'
  }]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall5d128f803a6476bd.id,
      key: _ctx.$citryPrepared.calls.citryCall5d128f803a6476bd.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Add notification")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      items: _ctx.notices,
      onDismiss: id => _ctx.notices = _ctx.notices.filter(item => item.id !== id),
      "citry-id": _ctx.$citryPrepared.calls.citryCall5d58bfc11d8e5f58.id,
      key: _ctx.$citryPrepared.calls.citryCall5d58bfc11d8e5f58.key
    }, null, 8 /* PROPS */, ["items", "onDismiss", "citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c81d8c878cdf5cd08ec72b4e1cc36ac78287863837a3f29ee97f614085db35a6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5d128f803a6476bd","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"notices = [...notices, {\n    id: `note-${next}`, title: `Observation ${next++} queued`, intent: 'info'\n  }]","sourceStart":60,"sourceEnd":176}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5d58bfc11d8e5f58","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[{"kind":"prop","name":":items","value":"notices","sourceStart":431,"sourceEnd":447},{"kind":"prop","name":":onDismiss","value":"id => notices = notices.filter(item => item.id !== id)","sourceStart":448,"sourceEnd":515}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_reactive_toast_queue_3acbcfd8 = _resolveComponent("citry-reactive-toast-queue-3acbcfd8")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_reactive_toast_queue_3acbcfd8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla1378e3a7772c988.id,
      key: _ctx.$citryPrepared.calls.citryCalla1378e3a7772c988.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["954d589b667e0f495295df0e9fe471607644f36a5598aad34b3435430ae76748"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla1378e3a7772c988","typeKey":"ReactiveToastQueue_66b64c","componentTag":"citry-reactive-toast-queue-3acbcfd8","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
