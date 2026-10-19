(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-badge",
    "data-citry-ui-part": "badge"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-badge__label",
      "data-citry-ui-part": "label"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot342d600796e3f7d6'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot342d600796e3f7d6", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["28e0caac0d7d346fa10c77ac00f6f9e77167a9c83fdbf28082bbabf644d0522d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_badge_20fd07c8 = _resolveComponent("citry-c-badge-20fd07c8")
  
  return (_openBlock(), _createElementBlock("nav", {
    class: "badge-counts",
    "aria-label": "Mineral archive queues"
  }, [
    _createElementVNode("a", {
      href: "#unfiled",
      "aria-label": "Unfiled specimens, 12 items"
    }, [
      _createElementVNode("span", null, "Unfiled specimens"),
      (_openBlock(), _createBlock(_component_citry_c_badge_20fd07c8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall3700ca1793168e95.id,
        key: _ctx.$citryPrepared.calls.citryCall3700ca1793168e95.key
      }, {
        ['citrySlot342d600796e3f7d6']: _withCtx(() => [
          _createTextVNode("12")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("a", {
      href: "#review",
      "aria-label": "Awaiting review, 4 items"
    }, [
      _createElementVNode("span", null, "Awaiting review"),
      (_openBlock(), _createBlock(_component_citry_c_badge_20fd07c8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall8865d07ca456ca06.id,
        key: _ctx.$citryPrepared.calls.citryCall8865d07ca456ca06.key
      }, {
        ['citrySlot342d600796e3f7d6']: _withCtx(() => [
          _createTextVNode("4")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e82bfb2b36c2c9ed053856beeb3e0551a93b8e390496f4e4737abccfd640f7ee"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3700ca1793168e95","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8865d07ca456ca06","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_badge_counts_and_context_2ee4e57d = _resolveComponent("citry-badge-counts-and-context-2ee4e57d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_badge_counts_and_context_2ee4e57d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallc1a6997b27a3a305.id,
      key: _ctx.$citryPrepared.calls.citryCallc1a6997b27a3a305.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b9a4ea160bbc104dda763df25cd8beabe8223b3e66544c6bc1199a54b1cd9064"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc1a6997b27a3a305","typeKey":"BadgeCountsAndContext_63e726","componentTag":"citry-badge-counts-and-context-2ee4e57d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
