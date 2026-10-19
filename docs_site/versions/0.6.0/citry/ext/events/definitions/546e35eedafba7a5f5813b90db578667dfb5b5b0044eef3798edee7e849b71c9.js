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
window.__citryRuntimeDefinitions["c2a894e92d43fb6c223c81a1d410321de62120cb10ad28d35ad8c3aec169ac52"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, withDirectives: _withDirectives, withModifiers: _withModifiers, createElementVNode: _createElementVNode, normalizeStyle: _normalizeStyle, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_form_54ae8704 = _resolveComponent("citry-c-form-54ae8704")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "night-checklist",
    style: _normalizeStyle({ colorScheme: _ctx.scheme, '--cui-form-gap': _ctx.gap }),
    "data-compact": _ctx.compact
  }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Night checklist"),
      _createElementVNode("h2", null, "Prepare the observatory")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_form_54ae8704, {
      onSubmit: _withModifiers($event => (void 0), ["prevent"]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall67870a2e6b89540d.id,
      key: _ctx.$citryPrepared.calls.citryCall67870a2e6b89540d.key
    }, {
      ['citrySlotf39a0a3e8a179bdf']: _withCtx(() => [
        _createElementVNode("label", null, [
          _withDirectives(_createElementVNode("input", {
            type: "checkbox",
            name: "task",
            value: "dome"
          }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ]),
          _createTextVNode(" Open the dome shutters ")
        ]),
        _createElementVNode("label", null, [
          _withDirectives(_createElementVNode("input", {
            type: "checkbox",
            name: "task",
            value: "cooling"
          }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ]),
          _createTextVNode(" Start detector cooling ")
        ]),
        _createElementVNode("label", null, [
          _withDirectives(_createElementVNode("input", {
            type: "checkbox",
            name: "task",
            value: "weather"
          }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ]),
          _createTextVNode(" Confirm weather limits ")
        ]),
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall34bcecc9569316c7.id,
          key: _ctx.$citryPrepared.calls.citryCall34bcecc9569316c7.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Begin session ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onSubmit", "citry-id"]))
  ], 12 /* STYLE, PROPS */, ["data-compact"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["36352afc7112442d49bff040b8f99c6729e2639daee29c15824d8c3e3a9a93d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall34bcecc9569316c7","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall67870a2e6b89540d","typeKey":"CForm_4a6900","componentTag":"citry-c-form-54ae8704","bindings":[{"kind":"event","name":"@submit.prevent","value":"void 0","sourceStart":228,"sourceEnd":252}],"fills":[{"name":"citrySlotf39a0a3e8a179bdf","localDescendants":["citryCall34bcecc9569316c7"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_form_theme_customization_655cf499 = _resolveComponent("citry-form-theme-customization-655cf499")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_form_theme_customization_655cf499, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb45cb21fa5eb13c3.id,
      key: _ctx.$citryPrepared.calls.citryCallb45cb21fa5eb13c3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["0ecd3bd196af0530abe2056f9a33afb2e0f51f85b04956d5401a494f896ebc26"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb45cb21fa5eb13c3","typeKey":"FormThemeCustomization_63ce7c","componentTag":"citry-form-theme-customization-655cf499","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
