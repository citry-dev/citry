(function(Vue){

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return null
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["93607fe0378a640d31ca9e8b837157c2bda24613f545d1e032dd47244d5e325e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, renderSlot: _renderSlot, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock(_Fragment, null, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot60c5ca9af814f9ad'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot60c5ca9af814f9ad", { key: 0 })
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
              (_ctx.$citryPrepared.selectedSlots['citrySlot69074d40f9608cc6'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot69074d40f9608cc6", { key: _ctx.$citryPrepared.slotKeys['citrySlot69074d40f9608cc6'], key: _ctx.$citryPrepared.slotKeys['citrySlot69074d40f9608cc6'] })
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b572890a2a8a7c47a938f8d41bca262dd69cd24d402e4fc78d3e4865019dd32f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      "citry-id": _ctx.$citryPrepared.calls.citryCall407f1496d79d7783.id,
      key: _ctx.$citryPrepared.calls.citryCall407f1496d79d7783.key
    }, {
      ['citrySlot60c5ca9af814f9ad']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_form_collection_item_2a143ed3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallb36cdc90bb062aee.id,
          key: _ctx.$citryPrepared.calls.citryCallb36cdc90bb062aee.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlot69074d40f9608cc6']: _withCtx(() => [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["391a96853d8ebe5b30009c9fe793b604963921233fd9d822683afdb83c207139"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb36cdc90bb062aee","typeKey":"CFormCollectionItem_089188","componentTag":"citry-c-form-collection-item-2a143ed3","bindings":[]},{"localId":"citryCall407f1496d79d7783","typeKey":"CFormCollection_1363aa","componentTag":"citry-c-form-collection-ce58b18b","bindings":[{"kind":"prop","name":":onAction","value":"applyCollectionAction","sourceStart":126,"sourceEnd":159}],"fills":[{"name":"citrySlot60c5ca9af814f9ad","localDescendants":["citryCallb36cdc90bb062aee"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot69074d40f9608cc6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_form_collection_server_actions_88578b4d = _resolveComponent("citry-form-collection-server-actions-88578b4d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_form_collection_server_actions_88578b4d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0ad6bd5ff55a0d28.id,
      key: _ctx.$citryPrepared.calls.citryCall0ad6bd5ff55a0d28.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5d79d66f2c7f0cf55d9704460e878c62b85e722c33288713a72b7502ae8dbbb7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0ad6bd5ff55a0d28","typeKey":"FormCollectionServerActions_648b9d","componentTag":"citry-form-collection-server-actions-88578b4d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
