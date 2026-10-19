(function(Vue){

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return null
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6b481192066e7fed9f5e2a7892387b480b6507e34dc9bbdba46bdfb0d14fa8b7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, renderSlot: _renderSlot, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock(_Fragment, null, [
    (_ctx.$citryPrepared.selectedSlots['citrySlotbed143ad7d28bfaf'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotbed143ad7d28bfaf", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("fieldset", _mergeProps({
      ref: "root",
      class: "cui-form-collection",
      "data-citry-ui-part": "form-collection"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("legend", _mergeProps({ "data-citry-ui-part": "legend" }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
      _createElementVNode("ol", { "data-citry-ui-part": "items" }, [
        (_openBlock(), _createElementBlock("li", _mergeProps({
          class: "cui-form-collection__item",
          "data-citry-form-collection-item": "",
          "data-citry-ui-part": "item"
        }, _ctx.$citryPrepared.citryAttrs2, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("div", _mergeProps({ role: "group" }, _ctx.$citryPrepared.citryAttrs3), [
            _createElementVNode("header", { "data-citry-ui-part": "item-header" }, [
              _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "item-label" }, _ctx.$citryPrepared.citryAttrs4), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */),
              _createElementVNode("div", { "data-citry-ui-part": "item-actions" }, [
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "move-up" }, _ctx.$citryPrepared.citryAttrs5), "↑", 16 /* FULL_PROPS */),
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "move-down" }, _ctx.$citryPrepared.citryAttrs6), "↓", 16 /* FULL_PROPS */),
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "remove" }, _ctx.$citryPrepared.citryAttrs7), "×", 16 /* FULL_PROPS */)
              ])
            ]),
            _createElementVNode("div", { "data-citry-ui-part": "item-content" }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlot5fe9f6e210f02f77'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot5fe9f6e210f02f77", { key: _ctx.$citryPrepared.slotKeys['citrySlot5fe9f6e210f02f77'], key: _ctx.$citryPrepared.slotKeys['citrySlot5fe9f6e210f02f77'] })
                : _createCommentVNode("v-if", true)
            ])
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ]),
      _createElementVNode("button", _mergeProps({
        "data-citry-form-collection-action": "add",
        "data-citry-ui-part": "add"
      }, _ctx.$citryPrepared.citryAttrs8), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 64 /* STABLE_FRAGMENT */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["caa0a46b871ebd61c95713b9bc2d7e4fdb7bda88e90e6fa7f0041359bb8a03ac"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, withDirectives: _withDirectives, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_form_collection_item_2a143ed3 = _resolveComponent("citry-c-form-collection-item-2a143ed3")
  const _component_citry_c_form_collection_ce58b18b = _resolveComponent("citry-c-form-collection-ce58b18b")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("form", {
    method: "post",
    action: "/team",
    onSubmit: _withModifiers($event => (_ctx.collectionStatus = 'Saved locally'), ["prevent"])
  }, [
    (_openBlock(), _createBlock(_component_citry_c_form_collection_ce58b18b, {
      onAction: _ctx.applyCollectionAction,
      "citry-id": _ctx.$citryPrepared.calls.citryCallcc5063a347c24bc7.id,
      key: _ctx.$citryPrepared.calls.citryCallcc5063a347c24bc7.key
    }, {
      ['citrySlotbed143ad7d28bfaf']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_form_collection_item_2a143ed3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallcc0c300cd5b3cf12.id,
          key: _ctx.$citryPrepared.calls.citryCallcc0c300cd5b3cf12.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlot5fe9f6e210f02f77']: _withCtx(() => [
        _withDirectives(_createElementVNode("input", {
          type: "hidden",
          name: "members[member-17][id]",
          value: "17"
        }, null, 512 /* NEED_PATCH */), [
          [_directive_citry_vue_owned, []]
        ]),
        _createElementVNode("label", null, [
          _createTextVNode("Role "),
          _withDirectives(_createElementVNode("input", {
            name: "members[member-17][role]",
            value: "Owner",
            required: ""
          }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ])
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onAction", "citry-id"])),
    _createElementVNode("button", { type: "submit" }, "Save team"),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.collectionStatus)
    }, "Order: Ada", 8 /* PROPS */, ["textContent"])
  ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b121180f16edf8410718cd3cad32679e8ecee1d47c95b34d5a8dc1c6bb2cbe42"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcc0c300cd5b3cf12","typeKey":"CFormCollectionItem_089188","componentTag":"citry-c-form-collection-item-2a143ed3","bindings":[]},{"localId":"citryCallcc5063a347c24bc7","typeKey":"CFormCollection_1363aa","componentTag":"citry-c-form-collection-ce58b18b","bindings":[{"kind":"prop","name":":onAction","value":"applyCollectionAction","sourceStart":126,"sourceEnd":159}],"fills":[{"name":"citrySlot5fe9f6e210f02f77","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotbed143ad7d28bfaf","localDescendants":["citryCallcc0c300cd5b3cf12"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_form_collection_server_actions_efc16ea2 = _resolveComponent("citry-form-collection-server-actions-efc16ea2")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_form_collection_server_actions_efc16ea2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4d11adec82c30d3c.id,
      key: _ctx.$citryPrepared.calls.citryCall4d11adec82c30d3c.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["bcececbb72130a71f525f568e4ba9631cfb626a46b7b4ff5117d12e2b69df868"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4d11adec82c30d3c","typeKey":"FormCollectionServerActions_498cd6","componentTag":"citry-form-collection-server-actions-efc16ea2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
