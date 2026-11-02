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
      value: _ctx.chosen,
      onValueChange: (value) => _ctx.chosen = value,
      "citry-id": _ctx.$citryPrepared.calls.citryCall2aee5c1fe3f7b655.id,
      key: _ctx.$citryPrepared.calls.citryCall2aee5c1fe3f7b655.key
    }, {
      ['citrySlot2b39ebfa2618df00']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall4f9598c56dbc01a0.id,
          key: _ctx.$citryPrepared.calls.citryCall4f9598c56dbc01a0.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Quiet")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallec0a974d5e4ee1a3.id,
          key: _ctx.$citryPrepared.calls.citryCallec0a974d5e4ee1a3.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Bright")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallc910ba48267b73d5.id,
          key: _ctx.$citryPrepared.calls.citryCallc910ba48267b73d5.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Central")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["value", "onValueChange", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.chosen.join(', '))
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4910d36b7b855f8f43e516eed041a69a68164af1caa2a2e309aecf8e6433d752"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4f9598c56dbc01a0","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallec0a974d5e4ee1a3","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc910ba48267b73d5","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2aee5c1fe3f7b655","typeKey":"CTagGroup_765ed5","componentTag":"citry-c-tag-group-b31ef680","bindings":[{"kind":"prop","name":":value","value":"chosen","sourceStart":65,"sourceEnd":80},{"kind":"prop","name":":onValueChange","value":"(value) => chosen = value","sourceStart":81,"sourceEnd":123}],"fills":[{"name":"citrySlot2b39ebfa2618df00","localDescendants":["citryCall4f9598c56dbc01a0","citryCallc910ba48267b73d5","citryCallec0a974d5e4ee1a3"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tag_selection_aa639667 = _resolveComponent("citry-tag-selection-aa639667")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tag_selection_aa639667, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall23d065c26ab8eb3d.id,
      key: _ctx.$citryPrepared.calls.citryCall23d065c26ab8eb3d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["566b17c43efc637b93cebc863b793d0d9c3475394f3bcaf1e61dcc0c9523b35b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall23d065c26ab8eb3d","typeKey":"TagSelection_f90120","componentTag":"citry-tag-selection-aa639667","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
