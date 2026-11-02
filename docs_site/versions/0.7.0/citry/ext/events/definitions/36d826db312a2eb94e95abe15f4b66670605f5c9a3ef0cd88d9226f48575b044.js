(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tag",
    "data-citry-ui-part": "tag"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", _mergeProps({ class: "cui-tag__cell" }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("span", _mergeProps({
        class: "cui-tag__indicator",
        "data-citry-ui-part": "indicator",
        "aria-hidden": "true"
      }, _ctx.$citryPrepared.citryAttrs2), "✓", 16 /* FULL_PROPS */),
      _createElementVNode("span", _mergeProps({
        class: "cui-tag__label",
        "data-citry-ui-part": "tag-label"
      }, _ctx.$citryPrepared.citryAttrs3), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1d0601d127842238'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1d0601d127842238", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["eb411f4bae1ca1a3d7dac3db7182aed7c24b1c60dbeac150f0fa92a05c0aa531"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tag-group",
    "data-citry-ui-part": "tag-group"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({
      class: "cui-tag-group__label",
      "data-citry-ui-part": "group-label"
    }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      class: "cui-tag-group__list",
      "data-citry-ui-part": "list"
    }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot2b39ebfa2618df00'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot2b39ebfa2618df00", { key: 0 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["98890a0395de46d1871c4922f1ea7ca759f5bcea52ac43f3b344605fb57c1b19"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tag_a351d619 = _resolveComponent("citry-c-tag-a351d619")
  const _component_citry_c_tag_group_b31ef680 = _resolveComponent("citry-c-tag-group-b31ef680")
  
  return (_openBlock(), _createElementBlock("div", { class: "citry-ui-demo-stack" }, [
    (_openBlock(), _createBlock(_component_citry_c_tag_group_b31ef680, {
      onAction: (value) => _ctx.last = value,
      "citry-id": _ctx.$citryPrepared.calls.citryCall9575f1d7c30fb815.id,
      key: _ctx.$citryPrepared.calls.citryCall9575f1d7c30fb815.key
    }, {
      ['citrySlot2b39ebfa2618df00']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallf36995ccab5c9776.id,
          key: _ctx.$citryPrepared.calls.citryCallf36995ccab5c9776.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Overview")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallb9056bea09edeaef.id,
          key: _ctx.$citryPrepared.calls.citryCallb9056bea09edeaef.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Activity")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall0f5b380b6bfaaea2.id,
          key: _ctx.$citryPrepared.calls.citryCall0f5b380b6bfaaea2.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Settings")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onAction", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Last action: ${_ctx.last}`)
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["78f1d80de7c7e87975016ac6bf727d2fc93452b2f864570eec87c06be1feaf7d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf36995ccab5c9776","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb9056bea09edeaef","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0f5b380b6bfaaea2","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9575f1d7c30fb815","typeKey":"CTagGroup_765ed5","componentTag":"citry-c-tag-group-b31ef680","bindings":[{"kind":"prop","name":":onAction","value":"(value) => last = value","sourceStart":65,"sourceEnd":100}],"fills":[{"name":"citrySlot2b39ebfa2618df00","localDescendants":["citryCall0f5b380b6bfaaea2","citryCallb9056bea09edeaef","citryCallf36995ccab5c9776"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tag_actions_77be095f = _resolveComponent("citry-tag-actions-77be095f")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tag_actions_77be095f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle3fcc450fffbae74.id,
      key: _ctx.$citryPrepared.calls.citryCalle3fcc450fffbae74.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6e9f5d81c768cd23692a8769210ff8fc6b1c459b5a34188cbf6833f44bd70fd8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle3fcc450fffbae74","typeKey":"TagActions_d82ab3","componentTag":"citry-tag-actions-77be095f","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
