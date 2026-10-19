(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-checkbox",
    "data-citry-ui-part": "checkbox"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-checkbox__input",
      type: "checkbox",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", { class: "cui-checkbox__body" }, [
      _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlotee4ced8dcf18698d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotee4ced8dcf18698d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e462caa5aa7997f643f793039dd60f5221538c17b95c9302d537ef71ce05e1e9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_checkbox_eb6eae85 = _resolveComponent("citry-c-checkbox-eb6eae85")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "checkbox-matrix",
    "aria-label": "Checkbox variants and sizes"
  }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf018fbf95a65026d.id,
        key: _ctx.$citryPrepared.calls.citryCallf018fbf95a65026d.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallffe759a85f22bf70.id,
        key: _ctx.$citryPrepared.calls.citryCallffe759a85f22bf70.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall31ef906b51fdb1f8.id,
        key: _ctx.$citryPrepared.calls.citryCall31ef906b51fdb1f8.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallbded2415e50b1830.id,
        key: _ctx.$citryPrepared.calls.citryCallbded2415e50b1830.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Partly cataloged collection ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall3af0b49c95d09cd5.id,
        key: _ctx.$citryPrepared.calls.citryCall3af0b49c95d09cd5.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Locked archive record ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallb2367bb4fbc827e4.id,
        key: _ctx.$citryPrepared.calls.citryCallb2367bb4fbc827e4.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Provenance needs review ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf9b8078d5fc91d61.id,
        key: _ctx.$citryPrepared.calls.citryCallf9b8078d5fc91d61.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallb0de31b2582b15b4.id,
        key: _ctx.$citryPrepared.calls.citryCallb0de31b2582b15b4.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallbdead0d5915d4544.id,
        key: _ctx.$citryPrepared.calls.citryCallbdead0d5915d4544.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall603c4465e19ecea2.id,
        key: _ctx.$citryPrepared.calls.citryCall603c4465e19ecea2.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Partly cataloged collection ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallaa25514e94dc7632.id,
        key: _ctx.$citryPrepared.calls.citryCallaa25514e94dc7632.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Locked archive record ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall4f2f7c877b5a70c1.id,
        key: _ctx.$citryPrepared.calls.citryCall4f2f7c877b5a70c1.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Provenance needs review ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a44b5e652116e646377165be5a09f7eb2553f5f9310587c703295d89a38ece00"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf018fbf95a65026d","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallffe759a85f22bf70","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall31ef906b51fdb1f8","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbded2415e50b1830","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3af0b49c95d09cd5","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb2367bb4fbc827e4","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf9b8078d5fc91d61","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb0de31b2582b15b4","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbdead0d5915d4544","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall603c4465e19ecea2","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallaa25514e94dc7632","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4f2f7c877b5a70c1","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_variants_and_sizes_26c68f22 = _resolveComponent("citry-checkbox-variants-and-sizes-26c68f22")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_variants_and_sizes_26c68f22, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallf149da6c4c049ef2.id,
      key: _ctx.$citryPrepared.calls.citryCallf149da6c4c049ef2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8f23bd335f8094d79a61b4a3a5a1fec335160872e6abee96d58a85da088c7899"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf149da6c4c049ef2","typeKey":"CheckboxVariantsAndSizes_17377a","componentTag":"citry-checkbox-variants-and-sizes-26c68f22","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
