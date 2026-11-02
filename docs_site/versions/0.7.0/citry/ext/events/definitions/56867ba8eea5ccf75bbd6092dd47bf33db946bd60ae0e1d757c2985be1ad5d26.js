(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0ae9bcd2ec59fd8d1c2c346b8b4db85b8f7a40a7713b2485132d154d060338f4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", _mergeProps({
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), " * ", 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fcec8560113f1cb2757bbacf9b66e82df47bdaac4eb43c0ce5bffdb59636c061"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-3bed3ea0af7a1780", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotb13ff7dbfcd5f34a'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotb13ff7dbfcd5f34a", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0adfeb1903c9250150e0a3d058316d216477a18bf78a56c396d8635da8b31dce"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_file_input_47da4d8c = _resolveComponent("citry-c-file-input-47da4d8c")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall00a95826bf5ff4e1.id,
    key: _ctx.$citryPrepared.calls.citryCall00a95826bf5ff4e1.key
  }, {
    ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall778d1fefb586e620.id,
        key: _ctx.$citryPrepared.calls.citryCall778d1fefb586e620.key
      }, {
        ['citrySlote2526e6f745e4169']: _withCtx(() => [
          _createTextVNode("Take a photo")
        ]),
        ['citrySlot6f90e269deb4619c']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_file_input_47da4d8c, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall7e276c101637d284.id,
            key: _ctx.$citryPrepared.calls.citryCall7e276c101637d284.key
          }, null, 8 /* PROPS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallfcd6ee23e313b798.id,
        key: _ctx.$citryPrepared.calls.citryCallfcd6ee23e313b798.key
      }, {
        ['citrySlote2526e6f745e4169']: _withCtx(() => [
          _createTextVNode("Record a note")
        ]),
        ['citrySlot6f90e269deb4619c']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_file_input_47da4d8c, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall64d2a5bc7489b6fd.id,
            key: _ctx.$citryPrepared.calls.citryCall64d2a5bc7489b6fd.key
          }, null, 8 /* PROPS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4299bef7c632f293dc9cac6ff8fa2db5c2a6449f7ef41ec1861f0f90c70f756c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7e276c101637d284","typeKey":"CFileInput_4f6cdb","componentTag":"citry-c-file-input-47da4d8c","bindings":[]},{"localId":"citryCall778d1fefb586e620","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall7e276c101637d284"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall64d2a5bc7489b6fd","typeKey":"CFileInput_4f6cdb","componentTag":"citry-c-file-input-47da4d8c","bindings":[]},{"localId":"citryCallfcd6ee23e313b798","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall64d2a5bc7489b6fd"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall00a95826bf5ff4e1","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":["citryCall64d2a5bc7489b6fd","citryCall778d1fefb586e620","citryCall7e276c101637d284","citryCallfcd6ee23e313b798"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_file_capture_hints_f22a723e = _resolveComponent("citry-file-capture-hints-f22a723e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_file_capture_hints_f22a723e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall093c3e223a9712d3.id,
      key: _ctx.$citryPrepared.calls.citryCall093c3e223a9712d3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ffc05331e63f008049aa54ae460906b33d23afbb756be939001cb5abd35fce84"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall093c3e223a9712d3","typeKey":"FileCaptureHints_15194f","componentTag":"citry-file-capture-hints-f22a723e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
