(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-combobox",
    "data-citry-combobox-root": "",
    "data-citry-ui-part": "root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-combobox__control",
      "data-citry-ui-part": "control"
    }, [
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-combobox__input",
        type: "text",
        role: "combobox",
        "aria-autocomplete": "list",
        readonly: "",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ]),
      _createElementVNode("button", _mergeProps({
        class: "cui-combobox__clear",
        type: "button",
        tabindex: "-1",
        "data-citry-combobox-clear": "",
        "data-citry-ui-part": "clear"
      }, _ctx.$citryPrepared.citryAttrs2), [
        _createElementVNode("span", { "aria-hidden": "true" }, " × ")
      ], 16 /* FULL_PROPS */),
      _createElementVNode("button", _mergeProps({
        class: "cui-combobox__trigger",
        type: "button",
        "aria-haspopup": "listbox",
        tabindex: "-1",
        "data-citry-combobox-trigger": "",
        "data-citry-ui-part": "trigger"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", { "aria-hidden": "true" }, " ▾ ")
      ], 16 /* FULL_PROPS */)
    ]),
    _withDirectives(_createElementVNode("input", {
      type: "hidden",
      "data-citry-combobox-form-value": ""
    }, null, 512 /* NEED_PATCH */), [
      [_directive_citry_vue_owned, []]
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-combobox__popup",
      "data-citry-ui-part": "popup"
    }, _ctx.$citryPrepared.citryAttrs4), [
      _createElementVNode("ul", _mergeProps({
        class: "cui-combobox__listbox",
        role: "listbox",
        "data-citry-ui-part": "listbox"
      }, _ctx.$citryPrepared.citryAttrs5), null, 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "loading"
      }, _ctx.$citryPrepared.citryAttrs6), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot6afdceafd772660c'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot6afdceafd772660c", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "empty"
      }, _ctx.$citryPrepared.citryAttrs7), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot0c2ff4fb678c9574'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot0c2ff4fb678c9574", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", {
        class: "cui-combobox__status cui-combobox__status--error",
        role: "status",
        "data-citry-ui-part": "error"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1fc1c3b10eb88fc4'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1fc1c3b10eb88fc4", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["36c29ab122fed2f33dae840fb4376ca86694ceadc2833c2d7bebfb8609a5eb98"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["173fb2f2aa6f6e87b26c18beae5ae339facef3620fae4bb8bef55081cbf8e0e5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_combobox_4720d729 = _resolveComponent("citry-c-combobox-4720d729")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createElementBlock("section", { class: "remote-stars" }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallff102ae3d004cc9f.id,
      key: _ctx.$citryPrepared.calls.citryCallff102ae3d004cc9f.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode(" Star catalog ")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_combobox_4720d729, {
          loadOptions: _ctx.loadStars,
          "citry-id": _ctx.$citryPrepared.calls.citryCall0955b90f2e0b8f3d.id,
          key: _ctx.$citryPrepared.calls.citryCall0955b90f2e0b8f3d.key
        }, {
          ['citrySlot6afdceafd772660c']: _withCtx(() => [
            _createTextVNode(" Reading the catalog... ")
          ]),
          ['citrySlot0c2ff4fb678c9574']: _withCtx(() => [
            _createTextVNode(" No catalog match. ")
          ]),
          ['citrySlot1fc1c3b10eb88fc4']: _withCtx(() => [
            _createTextVNode(" The catalog could not be read. ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loadOptions", "citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createTextVNode(" Try Vega, Rigel, Sirius, or Betelgeuse. Type offline to preview recovery. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a6f8a8f4a6b52c0c37f4e9362a68f9ce4338b2a21af8543227997401f0594ba6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0955b90f2e0b8f3d","typeKey":"CCombobox_bdcbb7","componentTag":"citry-c-combobox-4720d729","bindings":[{"kind":"prop","name":":loadOptions","value":"loadStars","sourceStart":341,"sourceEnd":365}],"fills":[{"name":"citrySlot0c2ff4fb678c9574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot1fc1c3b10eb88fc4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6afdceafd772660c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallff102ae3d004cc9f","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall0955b90f2e0b8f3d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_remote_star_catalog_eb5b099c = _resolveComponent("citry-remote-star-catalog-eb5b099c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_remote_star_catalog_eb5b099c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcddfb61a9c762c0b.id,
      key: _ctx.$citryPrepared.calls.citryCallcddfb61a9c762c0b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9285079e7f00fa03c4ef393e392037c6477807a49759c4c186e4cb91c5e15ff3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcddfb61a9c762c0b","typeKey":"RemoteStarCatalog_0ebba2","componentTag":"citry-remote-star-catalog-eb5b099c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
