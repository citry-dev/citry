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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6e1554d25e44badc3c578ef388c32df94d1f66423af39ac3de671a8fb7dbefdf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        "citry-id": _ctx.$citryPrepared.calls.citryCalla91831a13ac7eb10.id,
        key: _ctx.$citryPrepared.calls.citryCalla91831a13ac7eb10.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall80503e408c97fc6b.id,
        key: _ctx.$citryPrepared.calls.citryCall80503e408c97fc6b.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallb04706c0eb55fd12.id,
        key: _ctx.$citryPrepared.calls.citryCallb04706c0eb55fd12.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalldabd7d28cb19c131.id,
        key: _ctx.$citryPrepared.calls.citryCalldabd7d28cb19c131.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Partly cataloged collection ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall0bf78e70030d0039.id,
        key: _ctx.$citryPrepared.calls.citryCall0bf78e70030d0039.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Locked archive record ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall0f6d5177efa489db.id,
        key: _ctx.$citryPrepared.calls.citryCall0f6d5177efa489db.key
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
        "citry-id": _ctx.$citryPrepared.calls.citryCall068c8608a322963f.id,
        key: _ctx.$citryPrepared.calls.citryCall068c8608a322963f.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall76c35cc7cf73fc5c.id,
        key: _ctx.$citryPrepared.calls.citryCall76c35cc7cf73fc5c.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall442214a9b6208c49.id,
        key: _ctx.$citryPrepared.calls.citryCall442214a9b6208c49.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7) + " preserved specimen ", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall9895cf86f9c259f2.id,
        key: _ctx.$citryPrepared.calls.citryCall9895cf86f9c259f2.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Partly cataloged collection ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall173d238ca4024c7d.id,
        key: _ctx.$citryPrepared.calls.citryCall173d238ca4024c7d.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Locked archive record ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallfac2b6605567cecc.id,
        key: _ctx.$citryPrepared.calls.citryCallfac2b6605567cecc.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Provenance needs review ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f99dc2fea90470493aacac60da581157fad0e0e3eddc25719bbb014d0196f0ef"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla91831a13ac7eb10","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall80503e408c97fc6b","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb04706c0eb55fd12","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalldabd7d28cb19c131","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0bf78e70030d0039","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0f6d5177efa489db","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall068c8608a322963f","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall76c35cc7cf73fc5c","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall442214a9b6208c49","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9895cf86f9c259f2","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall173d238ca4024c7d","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallfac2b6605567cecc","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_variants_and_sizes_1d09d716 = _resolveComponent("citry-checkbox-variants-and-sizes-1d09d716")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_variants_and_sizes_1d09d716, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9a2860fd5eaafd64.id,
      key: _ctx.$citryPrepared.calls.citryCall9a2860fd5eaafd64.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1ee905853a56e2db441f11b2e9deaae205486ffec31784590b6cf96706ed31bc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9a2860fd5eaafd64","typeKey":"CheckboxVariantsAndSizes_10cbd5","componentTag":"citry-checkbox-variants-and-sizes-1d09d716","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
