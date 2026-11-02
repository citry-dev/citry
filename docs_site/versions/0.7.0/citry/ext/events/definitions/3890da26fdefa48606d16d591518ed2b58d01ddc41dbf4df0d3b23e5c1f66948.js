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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5751fc437130fb501a56f6402563d40f37f2af30ff2db9dfb79273600a828647"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3f421ec728d1978d4dd9716cb301a6fdf6756cb711fb43633ec8ca8e514f0689"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      "citry-id": _ctx.$citryPrepared.calls.citryCallb54d5cb64f649f38.id,
      key: _ctx.$citryPrepared.calls.citryCallb54d5cb64f649f38.key
    }, {
      ['citrySlotbaa898c15f287610']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalla3dcf50be49c1ae6.id,
          key: _ctx.$citryPrepared.calls.citryCalla3dcf50be49c1ae6.key
        }, {
          ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
            _createTextVNode("Draft")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall000dff51887573e8.id,
          key: _ctx.$citryPrepared.calls.citryCall000dff51887573e8.key
        }, {
          ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
            _createTextVNode("Ready for review")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld32b015ac21f62ab.id,
          key: _ctx.$citryPrepared.calls.citryCalld32b015ac21f62ab.key
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d648abf4f3c19eee5c7a20e245990baef48b40765e71c36d17df50fabbe0cbf5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla3dcf50be49c1ae6","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall000dff51887573e8","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld32b015ac21f62ab","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb54d5cb64f649f38","typeKey":"CListbox_1a159f","componentTag":"citry-c-listbox-70ddc967","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":35,"sourceEnd":49},{"kind":"prop","name":":onValueChange","value":"(next) => value = next","sourceStart":50,"sourceEnd":89}],"fills":[{"name":"citrySlotbaa898c15f287610","localDescendants":["citryCall000dff51887573e8","citryCalla3dcf50be49c1ae6","citryCalld32b015ac21f62ab"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_listbox_51973b59 = _resolveComponent("citry-controlled-listbox-51973b59")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_listbox_51973b59, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalleb3e152f10101967.id,
      key: _ctx.$citryPrepared.calls.citryCalleb3e152f10101967.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["edcefbb99601d5992826a91d927f3a2896cdc0706b5dd289c99d26922d4778ea"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalleb3e152f10101967","typeKey":"ControlledListbox_e59921","componentTag":"citry-controlled-listbox-51973b59","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
