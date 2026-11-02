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
  
  return (_openBlock(), _createElementBlock("section", { class: "habitat-summary" }, [
    (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
      checked: _ctx.all,
      indeterminate: _ctx.mixed,
      onInput: $event => (_ctx.setAll($event.target.checked)),
      "citry-id": _ctx.$citryPrepared.calls.citryCall221c2ddccd4d4c51.id,
      key: _ctx.$citryPrepared.calls.citryCall221c2ddccd4d4c51.key
    }, {
      ['citrySlot46b79f3889e5731e']: _withCtx(() => [
        _createTextVNode("All survey habitats")
      ]),
      ['citrySlot77e9b36d74732681']: _withCtx(() => [
        _createElementVNode("span", {
          textContent: _toDisplayString(`${_ctx.count} of 3 selected`)
        }, null, 8 /* PROPS */, ["textContent"])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["checked", "indeterminate", "onInput", "citry-id"])),
    _createElementVNode("div", { class: "habitat-summary__children" }, [
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        checked: _ctx.meadow,
        onInput: $event => (_ctx.meadow = $event.target.checked),
        "citry-id": _ctx.$citryPrepared.calls.citryCall00a0a4c0af887431.id,
        key: _ctx.$citryPrepared.calls.citryCall00a0a4c0af887431.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Limestone meadow ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["checked", "onInput", "citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        checked: _ctx.woodland,
        onInput: $event => (_ctx.woodland = $event.target.checked),
        "citry-id": _ctx.$citryPrepared.calls.citryCall204860eb2a37c821.id,
        key: _ctx.$citryPrepared.calls.citryCall204860eb2a37c821.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Beech woodland ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["checked", "onInput", "citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        checked: _ctx.wetland,
        onInput: $event => (_ctx.wetland = $event.target.checked),
        "citry-id": _ctx.$citryPrepared.calls.citryCallc0e5db1a357d1cba.id,
        key: _ctx.$citryPrepared.calls.citryCallc0e5db1a357d1cba.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Reed wetland ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["checked", "onInput", "citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d6549e15f18094ea66d631362c48ddac3f75c1fb91152e5e577ea1f7a348f3a0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall221c2ddccd4d4c51","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":checked","value":"all","sourceStart":64,"sourceEnd":78},{"kind":"prop","name":":indeterminate","value":"mixed","sourceStart":79,"sourceEnd":101},{"kind":"event","name":"@input","value":"setAll($event.target.checked)","sourceStart":102,"sourceEnd":140}],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall00a0a4c0af887431","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":checked","value":"meadow","sourceStart":557,"sourceEnd":574},{"kind":"event","name":"@input","value":"meadow = $event.target.checked","sourceStart":575,"sourceEnd":614}],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall204860eb2a37c821","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":checked","value":"woodland","sourceStart":881,"sourceEnd":900},{"kind":"event","name":"@input","value":"woodland = $event.target.checked","sourceStart":901,"sourceEnd":942}],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc0e5db1a357d1cba","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[{"kind":"prop","name":":checked","value":"wetland","sourceStart":1207,"sourceEnd":1225},{"kind":"event","name":"@input","value":"wetland = $event.target.checked","sourceStart":1226,"sourceEnd":1266}],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_indeterminate_checkbox_a880e7c6 = _resolveComponent("citry-indeterminate-checkbox-a880e7c6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_indeterminate_checkbox_a880e7c6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall417b01ad26d863d2.id,
      key: _ctx.$citryPrepared.calls.citryCall417b01ad26d863d2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0a297b7c053f5b34921a668bd11664fdeb1d710281de189cf71597c8d06eda49"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall417b01ad26d863d2","typeKey":"IndeterminateCheckbox_7e620a","componentTag":"citry-indeterminate-checkbox-a880e7c6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
