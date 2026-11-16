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
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("section", { class: "button-form" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Field journal"),
      _createElementVNode("h2", null, "Record a woodland sighting")
    ]),
    _createElementVNode("form", {
      onSubmit: _withModifiers($event => (_ctx.result = `Recorded with ${$event.submitter.value}.`), ["prevent"]),
      onReset: $event => (_ctx.result = 'Journal reset.')
    }, [
      _createElementVNode("label", { for: "button-form-species" }, "Species"),
      _createElementVNode("input", {
        id: "button-form-species",
        name: "species",
        value: "Silver-washed fritillary"
      }),
      _createElementVNode("div", null, [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall893eaa3fbfe63f4a.id,
          key: _ctx.$citryPrepared.calls.citryCall893eaa3fbfe63f4a.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Record sighting ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall97b356c7be35ccab.id,
          key: _ctx.$citryPrepared.calls.citryCall97b356c7be35ccab.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Reset journal ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit", "onReset"]),
    _createElementVNode("p", {
      class: "button-form__result",
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.result)
    }, " No sighting recorded yet. ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["26fb51b29379eb8ff726b7650a5056a28863a8d4a069656f9150932ecee20f36"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall893eaa3fbfe63f4a","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall97b356c7be35ccab","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_button_native_forms_57f93d39 = _resolveComponent("citry-button-native-forms-57f93d39")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_button_native_forms_57f93d39, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall57e2be1220a5282e.id,
      key: _ctx.$citryPrepared.calls.citryCall57e2be1220a5282e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["cd33d9f902270cd1fdfa480fd613711159bc092d813ae96cf4e10711596950e5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall57e2be1220a5282e","typeKey":"ButtonNativeForms_88e23b","componentTag":"citry-button-native-forms-57f93d39","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
