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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0f33d496b71a20b9ad95bf939b3cf49a23e416edc91f625c2c4128e5bd6ac1ac"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["359fe9e8d3ec0b80760a2fbed6f40689a3b80f4f0b8ec82f283694b89fe890df"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3700ca1793168e95","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8865d07ca456ca06","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_badge_counts_and_context_3f67a1d7 = _resolveComponent("citry-badge-counts-and-context-3f67a1d7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_badge_counts_and_context_3f67a1d7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0a9ee39f7f6ad990.id,
      key: _ctx.$citryPrepared.calls.citryCall0a9ee39f7f6ad990.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0f47540c812a1eddeaad90d2ace1eed8cb8b7d3913b382d7984ee8c9cf2915f1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0a9ee39f7f6ad990","typeKey":"BadgeCountsAndContext_1910e6","componentTag":"citry-badge-counts-and-context-3f67a1d7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
