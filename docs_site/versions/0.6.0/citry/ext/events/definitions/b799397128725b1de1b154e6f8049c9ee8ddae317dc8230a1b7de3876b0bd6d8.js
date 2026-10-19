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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["eb20e67cdd6be68963f5ca2b31469fede0919246d1738547ee7ef5db1abff427"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", { class: "toast-example" }, [
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      onClick: $event => (_ctx.items = [{
    id: 'offline', title: 'Working offline', actionLabel: 'Retry',
    closeOnAction: false, durationMs: 0, intent: 'warn'
  }]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall3c04a1eafa26befd.id,
      key: _ctx.$citryPrepared.calls.citryCall3c04a1eafa26befd.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Show persistent action")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.result)
    }, null, 8 /* PROPS */, ["textContent"]),
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      items: _ctx.items,
      onAction: () => _ctx.result = 'Retry requested',
      onDismiss: id => _ctx.items = _ctx.items.filter(item => item.id !== id),
      "citry-id": _ctx.$citryPrepared.calls.citryCallab3295fac42d3b89.id,
      key: _ctx.$citryPrepared.calls.citryCallab3295fac42d3b89.key
    }, null, 8 /* PROPS */, ["items", "onAction", "onDismiss", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5e1ba5826e20a350a53688ba3afa12a906f6c41f987c89db06dea23c1691ab3e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3c04a1eafa26befd","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"items = [{\n    id: 'offline', title: 'Working offline', actionLabel: 'Retry',\n    closeOnAction: false, durationMs: 0, intent: 'warn'\n  }]","sourceStart":60,"sourceEnd":207}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallab3295fac42d3b89","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[{"kind":"prop","name":":items","value":"items","sourceStart":504,"sourceEnd":518},{"kind":"prop","name":":onAction","value":"() => result = 'Retry requested'","sourceStart":519,"sourceEnd":563},{"kind":"prop","name":":onDismiss","value":"id => items = items.filter(item => item.id !== id)","sourceStart":564,"sourceEnd":627}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_persistent_toast_action_887e3bde = _resolveComponent("citry-persistent-toast-action-887e3bde")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_persistent_toast_action_887e3bde, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallbe41454c3ca6873f.id,
      key: _ctx.$citryPrepared.calls.citryCallbe41454c3ca6873f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["d4e3ea6ec79cd6793c0224ec08fa3228ee0d162e8a924f6fa3c9bf3bebf8303f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbe41454c3ca6873f","typeKey":"PersistentToastAction_0d356b","componentTag":"citry-persistent-toast-action-887e3bde","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
