(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["82d2edcd8997aee724cdf441dbae43faf818d8a2de062a03d50d1b517dcdb8fc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      _createElementVNode("span", {
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, " * ")
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["16cda6cc549682aec61a8b482e9e07b2c080fc7f48abe0572d16d6759b2e8b52"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("form", _mergeProps({
    ref: "root",
    class: "cui-form",
    "data-citry-ui-part": "form"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("fieldset", {
      class: "cui-form__fieldset",
      "data-citry-ui-part": "fieldset"
    }, [
      _createElementVNode("legend", {
        hidden: "",
        "aria-hidden": "true"
      }),
      (_ctx.$citryPrepared.selectedSlots['citrySlotf39a0a3e8a179bdf'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotf39a0a3e8a179bdf", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5d6b0b2f0d45c6db5d5382b3a8a6b807df89cbe0aec45c83c8045db47e3ffe96"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_input_743f5a7c = _resolveComponent("citry-c-input-743f5a7c")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_form_54ae8704 = _resolveComponent("citry-c-form-54ae8704")
  
  return (_openBlock(), _createElementBlock("section", { class: "proposal-form" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Time allocation"),
      _createElementVNode("h2", null, "Submit a telescope proposal")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_form_54ae8704, {
      disabled: _ctx.disabled,
      onSubmit: _withModifiers($event => (
      _ctx.result = JSON.stringify(
        Object.fromEntries(new window.FormData($event.target, $event.submitter))
      )
    ), ["prevent"]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall2d4d207bb5c32409.id,
      key: _ctx.$citryPrepared.calls.citryCall2d4d207bb5c32409.key
    }, {
      ['citrySlotf39a0a3e8a179bdf']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall474a793bc1334655.id,
          key: _ctx.$citryPrepared.calls.citryCall474a793bc1334655.key
        }, {
          ['citrySlote2526e6f745e4169']: _withCtx(() => [
            _createTextVNode(" Proposal title ")
          ]),
          ['citrySlot6f90e269deb4619c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_input_743f5a7c, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall4630a57b5e29cb32.id,
              key: _ctx.$citryPrepared.calls.citryCall4630a57b5e29cb32.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallc9e850059c1056db.id,
          key: _ctx.$citryPrepared.calls.citryCallc9e850059c1056db.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Submit proposal ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["disabled", "onSubmit", "citry-id"])),
    _createElementVNode("div", { class: "proposal-form__external" }, [
      _createElementVNode("label", { for: "allocation-code" }, "External allocation code"),
      (_openBlock(), _createBlock(_component_citry_c_input_743f5a7c, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallbfaf2ca583645f56.id,
        key: _ctx.$citryPrepared.calls.citryCallbfaf2ca583645f56.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("small", null, "Owned by the Form, but outside its disabled fieldset."),
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1655189ee9d5f132.id,
        key: _ctx.$citryPrepared.calls.citryCall1655189ee9d5f132.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode(" Submit from outside ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _withDirectives(_createElementVNode("output", {
      key: "citryReplacementc05569e0688dff1ddfff8908ea69a4c289d1d6e12638299ba952098b186ad95b",
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.result)
    }, null, 8 /* PROPS */, ["textContent"]), [
      [_vShow, _ctx.result]
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["58083606f0f2668edc94a6c983124df71886dfdbfb0e6ef7aceefac6f7a100ee"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectiveacaa69f6107290914ecbae7b72b79c4266decaca3eb0f06427537d61ffd94f45D0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectiveacaa69f6107290914ecbae7b72b79c4266decaca3eb0f06427537d61ffd94f45","replacementKey":"citryReplacementc05569e0688dff1ddfff8908ea69a4c289d1d6e12638299ba952098b186ad95b","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall4630a57b5e29cb32","typeKey":"CInput_dc895e","componentTag":"citry-c-input-743f5a7c","bindings":[]},{"localId":"citryCall474a793bc1334655","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall4630a57b5e29cb32"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc9e850059c1056db","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2d4d207bb5c32409","typeKey":"CForm_4a6900","componentTag":"citry-c-form-54ae8704","bindings":[{"kind":"prop","name":":disabled","value":"disabled","sourceStart":150,"sourceEnd":170},{"kind":"event","name":"@submit.prevent","value":"\n      result = JSON.stringify(\n        Object.fromEntries(new window.FormData($event.target, $event.submitter))\n      )\n    ","sourceStart":171,"sourceEnd":314}],"fills":[{"name":"citrySlotf39a0a3e8a179bdf","localDescendants":["citryCall4630a57b5e29cb32","citryCall474a793bc1334655","citryCallc9e850059c1056db"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbfaf2ca583645f56","typeKey":"CInput_dc895e","componentTag":"citry-c-input-743f5a7c","bindings":[]},{"localId":"citryCall1655189ee9d5f132","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_external_controls_a9360215 = _resolveComponent("citry-external-controls-a9360215")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_external_controls_a9360215, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4823ac0b64178862.id,
      key: _ctx.$citryPrepared.calls.citryCall4823ac0b64178862.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["33524ddefc5779f48dc81cf83c6cee843753393dfed9a66404dee14c38f28dfd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4823ac0b64178862","typeKey":"ExternalControls_615f78","componentTag":"citry-external-controls-a9360215","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
