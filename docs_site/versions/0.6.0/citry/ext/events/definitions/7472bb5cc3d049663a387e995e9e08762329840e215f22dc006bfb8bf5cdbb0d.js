(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-listbox__option",
    role: "option",
    "data-citry-ui-part": "listbox-option"
  }, _ctx.$citryPrepared.citryAttrs0, { key: _ctx.$citryPrepared.citryKey0 }), [
    _createElementVNode("span", {
      class: "cui-listbox__indicator",
      "aria-hidden": "true",
      "data-citry-ui-part": "listbox-indicator"
    }),
    _createElementVNode("span", {
      class: "cui-listbox__option-copy",
      "data-citry-ui-part": "listbox-option-copy"
    }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-listbox__option-label",
        "data-cui-listbox-slot-region": "",
        "data-citry-ui-part": "listbox-option-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlotde4686eb3d6712cc'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotde4686eb3d6712cc", { key: _ctx.$citryPrepared.slotKeys['citrySlotde4686eb3d6712cc'], key: _ctx.$citryPrepared.slotKeys['citrySlotde4686eb3d6712cc'] })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["776301c96022d5da82031de562998eb4d1e2689b32b66c6c3ea771313217cb58"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-listbox",
    "data-citry-ui-part": "listbox-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", _mergeProps({
      class: "cui-listbox__label",
      "data-citry-ui-part": "listbox-label"
    }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      class: "cui-listbox__surface",
      role: "listbox",
      "data-citry-ui-part": "listbox"
    }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotbaa898c15f287610'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotbaa898c15f287610", { key: 0 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8dec3a09b16e5a791c3215523a3b6171d1cc1b09f87af4f0bce583b0a09884b1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_listbox_option_2bb5350b = _resolveComponent("citry-c-listbox-option-2bb5350b")
  const _component_citry_c_listbox_70ddc967 = _resolveComponent("citry-c-listbox-70ddc967")
  
  return (_openBlock(), _createElementBlock("div", null, [
    (_openBlock(), _createBlock(_component_citry_c_listbox_70ddc967, {
      value: _ctx.value,
      onValueChange: (next) => _ctx.value = next,
      "citry-id": _ctx.$citryPrepared.calls.citryCall3c3ad7cbf2726167.id,
      key: _ctx.$citryPrepared.calls.citryCall3c3ad7cbf2726167.key
    }, {
      ['citrySlotbaa898c15f287610']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall14febd2b3ba8109e.id,
          key: _ctx.$citryPrepared.calls.citryCall14febd2b3ba8109e.key
        }, {
          ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
            _createTextVNode("Draft")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1622c17ecf545bd5.id,
          key: _ctx.$citryPrepared.calls.citryCall1622c17ecf545bd5.key
        }, {
          ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
            _createTextVNode("Ready for review")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall119855ed10183363.id,
          key: _ctx.$citryPrepared.calls.citryCall119855ed10183363.key
        }, {
          ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
            _createTextVNode("Approved")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["value", "onValueChange", "citry-id"])),
    _createElementVNode("p", null, [
      _createTextVNode("Current: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.value)
      }, null, 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["48616737a33c5010634b4c106794a81a3adf4369269c98cc81512437d64ce933"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall14febd2b3ba8109e","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1622c17ecf545bd5","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall119855ed10183363","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3c3ad7cbf2726167","typeKey":"CListbox_1a159f","componentTag":"citry-c-listbox-70ddc967","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":35,"sourceEnd":49},{"kind":"prop","name":":onValueChange","value":"(next) => value = next","sourceStart":50,"sourceEnd":89}],"fills":[{"name":"citrySlotbaa898c15f287610","localDescendants":["citryCall119855ed10183363","citryCall14febd2b3ba8109e","citryCall1622c17ecf545bd5"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_listbox_2521962d = _resolveComponent("citry-controlled-listbox-2521962d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_listbox_2521962d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7ab1f5f1ecdb6f35.id,
      key: _ctx.$citryPrepared.calls.citryCall7ab1f5f1ecdb6f35.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["24d0e4f279547263f3fd138c7bb60384bf1b37af4febc1213f5c63e9d0e53e95"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7ab1f5f1ecdb6f35","typeKey":"ControlledListbox_20ae44","componentTag":"citry-controlled-listbox-2521962d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
