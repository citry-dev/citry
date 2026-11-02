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
      "citry-id": _ctx.$citryPrepared.calls.citryCallf1b558a34f1dcfca.id,
      key: _ctx.$citryPrepared.calls.citryCallf1b558a34f1dcfca.key
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bc572bc68ffc06aa67c4d8b8328ef4a45639b03ae2ddd88ed190ed2ea25be39f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf1b558a34f1dcfca","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":variant","value":"variant","sourceStart":163,"sourceEnd":181},{"kind":"prop","name":":size","value":"size","sourceStart":182,"sourceEnd":194},{"kind":"prop","name":":label_pos","value":"label_pos","sourceStart":195,"sourceEnd":217},{"kind":"prop","name":":checked","value":"checked","sourceStart":218,"sourceEnd":236},{"kind":"prop","name":":indeterminate","value":"indeterminate","sourceStart":237,"sourceEnd":267},{"kind":"prop","name":":required","value":"required","sourceStart":268,"sourceEnd":288},{"kind":"prop","name":":disabled","value":"disabled","sourceStart":289,"sourceEnd":309},{"kind":"prop","name":":invalid","value":"invalid","sourceStart":310,"sourceEnd":328},{"kind":"event","name":"@input","value":"checked = $event.target.checked; indeterminate = false","sourceStart":329,"sourceEnd":392}],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_configuration_e6585698 = _resolveComponent("citry-checkbox-configuration-e6585698")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_configuration_e6585698, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallc83dd289e2c71c2c.id,
      key: _ctx.$citryPrepared.calls.citryCallc83dd289e2c71c2c.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7c0cbe626101de74fbc162ae89c3a96a0b4d60c72f968a4d3af3c5233e4206c7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc83dd289e2c71c2c","typeKey":"CheckboxConfiguration_52bb33","componentTag":"citry-checkbox-configuration-e6585698","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
