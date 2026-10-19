(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("textarea", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
  ], 17 /* TEXT, FULL_PROPS */)), [
    [_directive_citry_vue_owned, 'value']
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["285906243380b4ffec5bf2afcfd5a6d3a7864f1d9747e20cc094fb630b4e0b97"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot853fef0ef19da02c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot853fef0ef19da02c", { key: 3 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6d88fa0fd63605379b44731298fee8e8f8459206973093215c42df774d5327b3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["81a1fc957f2a8755f8ce082405e4e351c8f4f04f20700087e02025fa7a4b1a92"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_textarea_aed6f868 = _resolveComponent("citry-c-textarea-aed6f868")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_form_54ae8704 = _resolveComponent("citry-c-form-54ae8704")
  
  return (_openBlock(), _createElementBlock("section", { class: "forest-report" }, [
    (_openBlock(), _createBlock(_component_citry_c_form_54ae8704, {
      onSubmit: _withModifiers($event => (_ctx.submitted = new window.FormData($event.target).get('habitat')), ["prevent"]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall69963939dfc36d19.id,
      key: _ctx.$citryPrepared.calls.citryCall69963939dfc36d19.key
    }, {
      ['citrySlotf39a0a3e8a179bdf']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall186ce1ada5a8488b.id,
          key: _ctx.$citryPrepared.calls.citryCall186ce1ada5a8488b.key
        }, {
          ['citrySlote2526e6f745e4169']: _withCtx(() => [
            _createTextVNode("Habitat report")
          ]),
          ['citrySlot6f90e269deb4619c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_textarea_aed6f868, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalla2f90075528d02d0.id,
              key: _ctx.$citryPrepared.calls.citryCalla2f90075528d02d0.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          ['citrySlote7646b39489ca911']: _withCtx(() => [
            _createTextVNode("Use 12 to 180 characters.")
          ]),
          ['citrySlot853fef0ef19da02c']: _withCtx(() => [
            _createTextVNode("Add a fuller habitat description.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        _createElementVNode("div", { class: "forest-report__actions" }, [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld13bc535d855bb3b.id,
            key: _ctx.$citryPrepared.calls.citryCalld13bc535d855bb3b.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode("Save report")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall8b1cb45c4fd08f79.id,
            key: _ctx.$citryPrepared.calls.citryCall8b1cb45c4fd08f79.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode("Reset")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _withDirectives(_createElementVNode("output", {
          key: "citryReplacement33802603bd6de269efde8311dfd36b924c5cb7402715bcdccd8e41db8126d4f0",
          textContent: _toDisplayString(_ctx.submitted)
        }, null, 8 /* PROPS */, ["textContent"]), [
          [_vShow, _ctx.submitted]
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onSubmit", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e83f866e528459670d50e71680dbd063fa55ba23a593920ba5a84d0f8f3e75d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectived247d6b0d4bbf954a4f018d6e6082dbdec33f3fe535cad8dd9f1784c8079de57D0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectived247d6b0d4bbf954a4f018d6e6082dbdec33f3fe535cad8dd9f1784c8079de57","replacementKey":"citryReplacement33802603bd6de269efde8311dfd36b924c5cb7402715bcdccd8e41db8126d4f0","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCalla2f90075528d02d0","typeKey":"CTextarea_8ea155","componentTag":"citry-c-textarea-aed6f868","bindings":[]},{"localId":"citryCall186ce1ada5a8488b","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCalla2f90075528d02d0"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot853fef0ef19da02c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld13bc535d855bb3b","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8b1cb45c4fd08f79","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall69963939dfc36d19","typeKey":"CForm_4a6900","componentTag":"citry-c-form-54ae8704","bindings":[{"kind":"event","name":"@submit.prevent","value":"submitted = new window.FormData($event.target).get('habitat')","sourceStart":58,"sourceEnd":137}],"fills":[{"name":"citrySlotf39a0a3e8a179bdf","localDescendants":["citryCall186ce1ada5a8488b","citryCall8b1cb45c4fd08f79","citryCalla2f90075528d02d0","citryCalld13bc535d855bb3b"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_textarea_validation_9ef7342b = _resolveComponent("citry-textarea-validation-9ef7342b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_textarea_validation_9ef7342b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall36f7b2cdf56ef5bd.id,
      key: _ctx.$citryPrepared.calls.citryCall36f7b2cdf56ef5bd.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["50ffac5cc958db996be089d43054365ca43db6a5bc893ac2f1e7f79eaeee801c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall36f7b2cdf56ef5bd","typeKey":"TextareaValidation_ed95b6","componentTag":"citry-textarea-validation-9ef7342b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
