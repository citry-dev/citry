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
              (_ctx.$citryPrepared.selectedSlots['citrySlot02e90515294d74a0'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot02e90515294d74a0", { key: _ctx.$citryPrepared.slotKeys['citrySlot02e90515294d74a0'], key: _ctx.$citryPrepared.slotKeys['citrySlot02e90515294d74a0'] })
                : _createCommentVNode("v-if", true)
            ])
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("li", _mergeProps({
          class: "cui-form-collection__item",
          "data-citry-form-collection-item": "",
          "data-citry-ui-part": "item"
        }, _ctx.$citryPrepared.citryAttrs8, { key: _ctx.$citryPrepared.citryKey1 }), [
          _createElementVNode("div", _mergeProps({ role: "group" }, _ctx.$citryPrepared.citryAttrs9), [
            _createElementVNode("header", { "data-citry-ui-part": "item-header" }, [
              _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "item-label" }, _ctx.$citryPrepared.citryAttrs10), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */),
              _createElementVNode("div", { "data-citry-ui-part": "item-actions" }, [
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "move-up" }, _ctx.$citryPrepared.citryAttrs11), "↑", 16 /* FULL_PROPS */),
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "move-down" }, _ctx.$citryPrepared.citryAttrs12), "↓", 16 /* FULL_PROPS */),
                _createElementVNode("button", _mergeProps({ "data-citry-form-collection-action": "remove" }, _ctx.$citryPrepared.citryAttrs13), "×", 16 /* FULL_PROPS */)
              ])
            ]),
            _createElementVNode("div", { "data-citry-ui-part": "item-content" }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlotc8e0a48a85a749f7'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotc8e0a48a85a749f7", { key: _ctx.$citryPrepared.slotKeys['citrySlotc8e0a48a85a749f7'], key: _ctx.$citryPrepared.slotKeys['citrySlotc8e0a48a85a749f7'] })
                : _createCommentVNode("v-if", true)
            ])
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ]),
      _createElementVNode("button", _mergeProps({
        "data-citry-form-collection-action": "add",
        "data-citry-ui-part": "add"
      }, _ctx.$citryPrepared.citryAttrs14), _toDisplayString(_ctx.$citryPrepared.citryText3), 17 /* TEXT, FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 64 /* STABLE_FRAGMENT */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3950b0b4f04f7ebc2c1e7e6c6e5ddc24c6c6af0694d3f8dbf2397f86965d88d6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_form_collection_item_2a143ed3 = _resolveComponent("citry-c-form-collection-item-2a143ed3")
  const _component_citry_c_form_collection_ce58b18b = _resolveComponent("citry-c-form-collection-ce58b18b")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", null, [
    (_openBlock(), _createBlock(_component_citry_c_form_collection_ce58b18b, {
      onAction: _ctx.applyCollectionAction,
      "citry-id": _ctx.$citryPrepared.calls.citryCall089749e310bf3bba.id,
      key: _ctx.$citryPrepared.calls.citryCall089749e310bf3bba.key
    }, {
      ['citrySlot60c5ca9af814f9ad']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_form_collection_item_2a143ed3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallfd1d92e8eb9bf30e.id,
          key: _ctx.$citryPrepared.calls.citryCallfd1d92e8eb9bf30e.key
        }, null, 8 /* PROPS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_form_collection_item_2a143ed3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld3978ab13f9b0cdf.id,
          key: _ctx.$citryPrepared.calls.citryCalld3978ab13f9b0cdf.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlot02e90515294d74a0']: _withCtx(() => [
        _createElementVNode("label", null, [
          _createTextVNode("Number "),
          _withDirectives(_createElementVNode("input", { name: "phones[mobile]" }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ])
        ])
      ]),
      ['citrySlotc8e0a48a85a749f7']: _withCtx(() => [
        _createElementVNode("label", null, [
          _createTextVNode("Number "),
          _withDirectives(_createElementVNode("input", { name: "phones[office]" }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ])
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onAction", "citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.collectionStatus)
    }, "Order: Mobile, Office", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["feb2ce1cc24d9f2b95461383a4dbaba4959605881c1746a5cc429e34e3753cfd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfd1d92e8eb9bf30e","typeKey":"CFormCollectionItem_089188","componentTag":"citry-c-form-collection-item-2a143ed3","bindings":[]},{"localId":"citryCalld3978ab13f9b0cdf","typeKey":"CFormCollectionItem_089188","componentTag":"citry-c-form-collection-item-2a143ed3","bindings":[]},{"localId":"citryCall089749e310bf3bba","typeKey":"CFormCollection_1363aa","componentTag":"citry-c-form-collection-ce58b18b","bindings":[{"kind":"prop","name":":onAction","value":"applyCollectionAction","sourceStart":47,"sourceEnd":80}],"fills":[{"name":"citrySlot02e90515294d74a0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot60c5ca9af814f9ad","localDescendants":["citryCalld3978ab13f9b0cdf","citryCallfd1d92e8eb9bf30e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e0a48a85a749f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_form_collection_client_actions_88c63e83 = _resolveComponent("citry-form-collection-client-actions-88c63e83")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_form_collection_client_actions_88c63e83, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld7f359d98a10c784.id,
      key: _ctx.$citryPrepared.calls.citryCalld7f359d98a10c784.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["34456d0f67c51a693a9fea7391ccd5356ba5b4f1cb3cd7f1e8e426b25d6e239e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld7f359d98a10c784","typeKey":"FormCollectionClientActions_4f5535","componentTag":"citry-form-collection-client-actions-88c63e83","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
