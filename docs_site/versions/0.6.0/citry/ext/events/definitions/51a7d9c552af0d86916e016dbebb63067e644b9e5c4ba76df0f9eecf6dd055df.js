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
        (_ctx.$citryPrepared.selectedSlots['citrySlot87b6ce9877cfed3d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot87b6ce9877cfed3d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fe41160c82c3bd7367ae97f7d199c42a13d7f3381ea7c7379f44ba57353b182d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      (_ctx.$citryPrepared.selectedSlots['citrySlot35ca42a839393489'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot35ca42a839393489", { key: 0 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9fad5312de33f298754309a4373dc41513ba2f6b7edd040767ae5574a8cae3d8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      "citry-id": _ctx.$citryPrepared.calls.citryCall7d2fbbe471563e77.id,
      key: _ctx.$citryPrepared.calls.citryCall7d2fbbe471563e77.key
    }, {
      ['citrySlot35ca42a839393489']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall9dade30dad35a59b.id,
          key: _ctx.$citryPrepared.calls.citryCall9dade30dad35a59b.key
        }, {
          ['citrySlot87b6ce9877cfed3d']: _withCtx(() => [
            _createTextVNode("Quiet")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall690ac9ac73cabe2b.id,
          key: _ctx.$citryPrepared.calls.citryCall690ac9ac73cabe2b.key
        }, {
          ['citrySlot87b6ce9877cfed3d']: _withCtx(() => [
            _createTextVNode("Bright")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld1b9c6485dcc8bfd.id,
          key: _ctx.$citryPrepared.calls.citryCalld1b9c6485dcc8bfd.key
        }, {
          ['citrySlot87b6ce9877cfed3d']: _withCtx(() => [
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["aaee73de1463de926a424f20c747f74aac6784fcfad79c55ac32cacf69849600"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9dade30dad35a59b","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot87b6ce9877cfed3d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall690ac9ac73cabe2b","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot87b6ce9877cfed3d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld1b9c6485dcc8bfd","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot87b6ce9877cfed3d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7d2fbbe471563e77","typeKey":"CTagGroup_765ed5","componentTag":"citry-c-tag-group-b31ef680","bindings":[{"kind":"prop","name":":value","value":"chosen","sourceStart":65,"sourceEnd":80},{"kind":"prop","name":":onValueChange","value":"(value) => chosen = value","sourceStart":81,"sourceEnd":123}],"fills":[{"name":"citrySlot35ca42a839393489","localDescendants":["citryCall690ac9ac73cabe2b","citryCall9dade30dad35a59b","citryCalld1b9c6485dcc8bfd"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tag_selection_17096f66 = _resolveComponent("citry-tag-selection-17096f66")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tag_selection_17096f66, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall84fc8baef8aeff4b.id,
      key: _ctx.$citryPrepared.calls.citryCall84fc8baef8aeff4b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ba6d53f1bf2e48b6f9e90c2e3874c616bd8c750b83108ed6b120933ccddca504"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall84fc8baef8aeff4b","typeKey":"TagSelection_f1bf27","componentTag":"citry-tag-selection-17096f66","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
