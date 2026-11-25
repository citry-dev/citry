(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

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
      ], 16 /* FULL_PROPS */),
      _createElementVNode("button", _mergeProps({
        class: "cui-tag__remove",
        "data-citry-ui-part": "remove",
        type: "button",
        tabindex: "-1"
      }, _ctx.$citryPrepared.citryAttrs4), [
        _createElementVNode("span", _mergeProps({ class: "cui-tag__remove-text" }, _ctx.$citryPrepared.citryAttrs5), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
        _createElementVNode("span", { "aria-hidden": "true" }, "×")
      ], 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["427cae54a18b5352bdf3d90889ce5ffac1f5070965f9ffa5341b34b65a3f3f63"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      onRemove: (values) => _ctx.last = values.join(', '),
      "citry-id": _ctx.$citryPrepared.calls.citryCall1f9d61182a283b69.id,
      key: _ctx.$citryPrepared.calls.citryCall1f9d61182a283b69.key
    }, {
      ['citrySlot2b39ebfa2618df00']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1eeadc9cc627c6ee.id,
          key: _ctx.$citryPrepared.calls.citryCall1eeadc9cc627c6ee.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Design")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall8182a9d54abff52f.id,
          key: _ctx.$citryPrepared.calls.citryCall8182a9d54abff52f.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Research")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall4452f714d7a1c8a7.id,
          key: _ctx.$citryPrepared.calls.citryCall4452f714d7a1c8a7.key
        }, {
          ['citrySlot1d0601d127842238']: _withCtx(() => [
            _createTextVNode("Delivery")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onRemove", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Requested removal: ${_ctx.last}`)
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["51d3396ece409974ec4db5586f3e0b5d074c17da02917f3af785531b3ce3041c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1eeadc9cc627c6ee","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8182a9d54abff52f","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4452f714d7a1c8a7","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot1d0601d127842238","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1f9d61182a283b69","typeKey":"CTagGroup_765ed5","componentTag":"citry-c-tag-group-b31ef680","bindings":[{"kind":"prop","name":":onRemove","value":"(values) => last = values.join(', ')","sourceStart":65,"sourceEnd":113}],"fills":[{"name":"citrySlot2b39ebfa2618df00","localDescendants":["citryCall1eeadc9cc627c6ee","citryCall4452f714d7a1c8a7","citryCall8182a9d54abff52f"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tag_removal_584256fd = _resolveComponent("citry-tag-removal-584256fd")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tag_removal_584256fd, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla9dd317fc0cd8966.id,
      key: _ctx.$citryPrepared.calls.citryCalla9dd317fc0cd8966.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3c30e5a2853c861a4d145399cf0b9303737b7f7cac7dad0d5c74360465cc7c60"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla9dd317fc0cd8966","typeKey":"TagRemoval_98a061","componentTag":"citry-tag-removal-584256fd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
