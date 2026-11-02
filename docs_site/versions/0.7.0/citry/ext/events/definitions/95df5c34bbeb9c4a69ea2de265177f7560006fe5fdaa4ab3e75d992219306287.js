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
        (_ctx.$citryPrepared.selectedSlots['citrySlot46b79f3889e5731e'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot46b79f3889e5731e", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot77e9b36d74732681'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot77e9b36d74732681", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d37012a65a9c7e4d1e73a5117d2a3ad47d3a01ab5fe920180b47d12400e07e48"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

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
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["841349b9ea26722ddc97c6100ff42ff29b78b70d4b6e24579dd575fa477dea4a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_checkbox_eb6eae85 = _resolveComponent("citry-c-checkbox-eb6eae85")
  
  return (_openBlock(), _createElementBlock("section", { class: "checkbox-labels" }, [
    (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallbbaf1333009f16a7.id,
      key: _ctx.$citryPrepared.calls.citryCallbbaf1333009f16a7.key
    }, {
      ['citrySlot46b79f3889e5731e']: _withCtx(() => [
        _createTextVNode(" Preserve this unusually long field-note label when the observation is exported to the regional botanical archive ")
      ]),
      ['citrySlot77e9b36d74732681']: _withCtx(() => [
        _createTextVNode(" Logical start placement and narrow wrapping remain direction-aware. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", { dir: "rtl" }, [
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallce1068a7f9c11653.id,
        key: _ctx.$citryPrepared.calls.citryCallce1068a7f9c11653.key
      }, {
        ['citrySlot46b79f3889e5731e']: _withCtx(() => [
          _createTextVNode("تضمين ملاحظات الموطن")
        ]),
        ['citrySlot77e9b36d74732681']: _withCtx(() => [
          _createTextVNode("يبقى موضع التسمية منطقيًا في الاتجاه من اليمين.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("div", { class: "checkbox-labels__row" }, [
      _createElementVNode("span", null, "Polypody fern, row 17"),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallab4f8c616df78d7b.id,
        key: _ctx.$citryPrepared.calls.citryCallab4f8c616df78d7b.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c9e5eab09082966aec4eb20cd2136313e92fca03f752e20439f0fc699fa508bb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbbaf1333009f16a7","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallce1068a7f9c11653","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallab4f8c616df78d7b","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_labels_c7e19f0e = _resolveComponent("citry-checkbox-labels-c7e19f0e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_labels_c7e19f0e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0ceb3939ea6c363a.id,
      key: _ctx.$citryPrepared.calls.citryCall0ceb3939ea6c363a.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["90234f5f3a3ccf088cbcae019a069a5cc05ad202995783b06ffccdc483858dd2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0ceb3939ea6c363a","typeKey":"CheckboxLabels_bf6eab","componentTag":"citry-checkbox-labels-c7e19f0e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
