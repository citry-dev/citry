(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-editable",
    "data-citry-ui-part": "root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-editable__preview",
      "data-citry-ui-part": "preview"
    }, [
      _createElementVNode("span", { "data-citry-ui-part": "preview-value" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
      _createElementVNode("button", _mergeProps({
        class: "cui-editable__action cui-editable__edit",
        type: "button",
        "data-citry-ui-part": "edit-action"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("span", { "aria-hidden": "true" }, "✎")
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("div", {
      class: "cui-editable__edit-surface",
      "data-citry-ui-part": "edit-surface"
    }, [
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-editable__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ]),
      _createElementVNode("span", {
        class: "cui-editable__actions",
        "data-citry-ui-part": "actions"
      }, [
        _createElementVNode("button", _mergeProps({
          class: "cui-editable__action cui-editable__submit",
          type: "button",
          "data-citry-ui-part": "submit-action"
        }, _ctx.$citryPrepared.citryAttrs3), [
          _createElementVNode("span", { "aria-hidden": "true" }, "✓")
        ], 16 /* FULL_PROPS */),
        _createElementVNode("button", _mergeProps({
          class: "cui-editable__action cui-editable__cancel",
          type: "button",
          "data-citry-ui-part": "cancel-action"
        }, _ctx.$citryPrepared.citryAttrs4), [
          _createElementVNode("span", { "aria-hidden": "true" }, "✕")
        ], 16 /* FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e5ac1de59a82eb5a4fff7b08443faf8b2e44d78ff4645029c52fa980cca4940e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_editable_a4636eb1 = _resolveComponent("citry-c-editable-a4636eb1")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall34fa51b48d8899f9.id,
    key: _ctx.$citryPrepared.calls.citryCall34fa51b48d8899f9.key
  }, {
    ['citrySlote2526e6f745e4169']: _withCtx(() => [
      _createTextVNode("Project name")
    ]),
    ['citrySlot6f90e269deb4619c']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_editable_a4636eb1, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall63e39153206b74db.id,
        key: _ctx.$citryPrepared.calls.citryCall63e39153206b74db.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    ['citrySlote7646b39489ca911']: _withCtx(() => [
      _createTextVNode("Use the pencil to rename this project in place.")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ee563ddbe1bea641bdcfb4bfa18bfd0478c5448386be3b78ae394c0706e96b1f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall63e39153206b74db","typeKey":"CEditable_620b5b","componentTag":"citry-c-editable-a4636eb1","bindings":[]},{"localId":"citryCall34fa51b48d8899f9","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall63e39153206b74db"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_editable_at_a_glance_0cc25534 = _resolveComponent("citry-editable-at-a-glance-0cc25534")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_editable_at_a_glance_0cc25534, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5a4fd0e950c45eb6.id,
      key: _ctx.$citryPrepared.calls.citryCall5a4fd0e950c45eb6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["dce9b21c224cf2e3becda2866ba7736ad1c1e88d608e198fe42a385d45777f06"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5a4fd0e950c45eb6","typeKey":"EditableAtAGlance_fa8541","componentTag":"citry-editable-at-a-glance-0cc25534","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
