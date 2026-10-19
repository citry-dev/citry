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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4597559ea48af9645814a08a7023ccf51553b6cf852bf213eb5d2fb938fd8d50"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_checkbox_eb6eae85 = _resolveComponent("citry-c-checkbox-eb6eae85")
  
  return (_openBlock(), _createElementBlock("section", { class: "checkbox-configurator" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Living collection"),
      _createElementVNode("h2", null, "Configure the record marker")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
      variant: _ctx.variant,
      size: _ctx.size,
      label_pos: _ctx.label_pos,
      checked: _ctx.checked,
      indeterminate: _ctx.indeterminate,
      required: _ctx.required,
      disabled: _ctx.disabled,
      invalid: _ctx.invalid,
      onInput: $event => {_ctx.checked = $event.target.checked; _ctx.indeterminate = false},
      "citry-id": _ctx.$citryPrepared.calls.citryCalle1bc72877682bf24.id,
      key: _ctx.$citryPrepared.calls.citryCalle1bc72877682bf24.key
    }, {
      ['citrySlot46b79f3889e5731e']: _withCtx(() => [
        _createTextVNode("Verified against the herbarium sheet")
      ]),
      ['citrySlot77e9b36d74732681']: _withCtx(() => [
        _createTextVNode(" Match leaf shape, vein pattern, and collection date. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["variant", "size", "label_pos", "checked", "indeterminate", "required", "disabled", "invalid", "onInput", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4d061053bf3bc7b59c148c8d7645f4fe5af62c349812f8c5c93ce864c35c3fd5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle1bc72877682bf24","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":variant","value":"variant","sourceStart":163,"sourceEnd":181},{"kind":"prop","name":":size","value":"size","sourceStart":182,"sourceEnd":194},{"kind":"prop","name":":label_pos","value":"label_pos","sourceStart":195,"sourceEnd":217},{"kind":"prop","name":":checked","value":"checked","sourceStart":218,"sourceEnd":236},{"kind":"prop","name":":indeterminate","value":"indeterminate","sourceStart":237,"sourceEnd":267},{"kind":"prop","name":":required","value":"required","sourceStart":268,"sourceEnd":288},{"kind":"prop","name":":disabled","value":"disabled","sourceStart":289,"sourceEnd":309},{"kind":"prop","name":":invalid","value":"invalid","sourceStart":310,"sourceEnd":328},{"kind":"event","name":"@input","value":"checked = $event.target.checked; indeterminate = false","sourceStart":329,"sourceEnd":392}],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_configuration_2b37f4e7 = _resolveComponent("citry-checkbox-configuration-2b37f4e7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_configuration_2b37f4e7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla0a5ae8ed0f123c1.id,
      key: _ctx.$citryPrepared.calls.citryCalla0a5ae8ed0f123c1.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["686282514fe8405eec8c53e08de129488a63567e9ae0c49fe996f2c88123b205"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla0a5ae8ed0f123c1","typeKey":"CheckboxConfiguration_7a6b88","componentTag":"citry-checkbox-configuration-2b37f4e7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
