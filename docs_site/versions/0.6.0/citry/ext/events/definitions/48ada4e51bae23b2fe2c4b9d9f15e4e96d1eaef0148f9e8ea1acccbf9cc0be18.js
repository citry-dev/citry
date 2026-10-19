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
    class: "cui-listbox__group",
    role: "group",
    "data-citry-ui-part": "listbox-group"
  }, _ctx.$citryPrepared.citryAttrs0, { key: _ctx.$citryPrepared.citryKey0 }), [
    _createElementVNode("span", _mergeProps({
      class: "cui-listbox__group-label",
      "data-citry-ui-part": "listbox-group-label"
    }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
    (_ctx.$citryPrepared.selectedSlots['citrySlot636887442f7c4f3e'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot636887442f7c4f3e", { key: _ctx.$citryPrepared.slotKeys['citrySlot636887442f7c4f3e'], key: _ctx.$citryPrepared.slotKeys['citrySlot636887442f7c4f3e'] })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8f1aac59a34b5c9e20b50efe417ce12a58493eb84367274acbcde72db1c94eaa"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_listbox_option_2bb5350b = _resolveComponent("citry-c-listbox-option-2bb5350b")
  const _component_citry_c_listbox_group_8d4fc0e2 = _resolveComponent("citry-c-listbox-group-8d4fc0e2")
  const _component_citry_c_listbox_70ddc967 = _resolveComponent("citry-c-listbox-70ddc967")
  
  return (_openBlock(), _createBlock(_component_citry_c_listbox_70ddc967, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall477061b730356b6c.id,
    key: _ctx.$citryPrepared.calls.citryCall477061b730356b6c.key
  }, {
    ['citrySlotbaa898c15f287610']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_listbox_group_8d4fc0e2, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall55e6e1c5e429c992.id,
        key: _ctx.$citryPrepared.calls.citryCall55e6e1c5e429c992.key
      }, {
        ['citrySlot636887442f7c4f3e']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall844788aec5a47c05.id,
            key: _ctx.$citryPrepared.calls.citryCall844788aec5a47c05.key
          }, {
            ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
              _createTextVNode("Prague")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1967ef571503e447.id,
            key: _ctx.$citryPrepared.calls.citryCall1967ef571503e447.key
          }, {
            ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
              _createTextVNode("Lisbon")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_listbox_group_8d4fc0e2, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6ff6080be90a6457.id,
        key: _ctx.$citryPrepared.calls.citryCall6ff6080be90a6457.key
      }, {
        ['citrySlot636887442f7c4f3e']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalla3add452de0d0aaf.id,
            key: _ctx.$citryPrepared.calls.citryCalla3add452de0d0aaf.key
          }, {
            ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
              _createTextVNode("Kyoto")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_listbox_option_2bb5350b, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall2843182aefc4df29.id,
            key: _ctx.$citryPrepared.calls.citryCall2843182aefc4df29.key
          }, {
            ['citrySlotde4686eb3d6712cc']: _withCtx(() => [
              _createTextVNode("Wellington")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fd9dac553348b46cd59cd80f2f275e6aaa3cc22436b3d063cc0b9b6c5173aa69"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall844788aec5a47c05","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1967ef571503e447","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall55e6e1c5e429c992","typeKey":"CListboxGroup_3f3e4c","componentTag":"citry-c-listbox-group-8d4fc0e2","bindings":[],"fills":[{"name":"citrySlot636887442f7c4f3e","localDescendants":["citryCall1967ef571503e447","citryCall844788aec5a47c05"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla3add452de0d0aaf","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2843182aefc4df29","typeKey":"CListboxOption_dfb80c","componentTag":"citry-c-listbox-option-2bb5350b","bindings":[],"fills":[{"name":"citrySlotde4686eb3d6712cc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6ff6080be90a6457","typeKey":"CListboxGroup_3f3e4c","componentTag":"citry-c-listbox-group-8d4fc0e2","bindings":[],"fills":[{"name":"citrySlot636887442f7c4f3e","localDescendants":["citryCall2843182aefc4df29","citryCalla3add452de0d0aaf"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall477061b730356b6c","typeKey":"CListbox_1a159f","componentTag":"citry-c-listbox-70ddc967","bindings":[],"fills":[{"name":"citrySlotbaa898c15f287610","localDescendants":["citryCall1967ef571503e447","citryCall2843182aefc4df29","citryCall55e6e1c5e429c992","citryCall6ff6080be90a6457","citryCall844788aec5a47c05","citryCalla3add452de0d0aaf"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_grouped_options_2f0cde87 = _resolveComponent("citry-grouped-options-2f0cde87")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_grouped_options_2f0cde87, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2179d34ed1ca5ad9.id,
      key: _ctx.$citryPrepared.calls.citryCall2179d34ed1ca5ad9.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2122124c0bbd1c88d092b7eecd914778bc98c9b20d4ff69730acc1a6b0047207"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2179d34ed1ca5ad9","typeKey":"GroupedOptions_7b3ed9","componentTag":"citry-grouped-options-2f0cde87","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
