(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    ref: "root",
    class: "cui-infinite-scroll",
    "data-citry-ui-part": "infinite-scroll"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "content" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot2303c299128fad15'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot2303c299128fad15", { key: 0 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", {
      "data-citry-ui-part": "status",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true"
    }, [
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs3)), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */),
      _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
    ]),
    _createElementVNode("button", _mergeProps({
      "data-citry-infinite-scroll-action": "",
      "data-citry-ui-part": "action"
    }, _ctx.$citryPrepared.citryAttrs4), [
      _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs5)), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      "data-citry-infinite-scroll-sentinel": "",
      "data-citry-ui-part": "sentinel",
      "aria-hidden": "true"
    })
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["971e0d75eb8b44b14bab43bcf44cee62a1384112b4f5f27122201f98b157c418"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_infinite_scroll_3b75d624 = _resolveComponent("citry-c-infinite-scroll-3b75d624")
  
  return (_openBlock(), _createBlock(_component_citry_c_infinite_scroll_3b75d624, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall5de20a3ab63fdbf0.id,
    key: _ctx.$citryPrepared.calls.citryCall5de20a3ab63fdbf0.key
  }, {
    ['citrySlot2303c299128fad15']: _withCtx(() => [
      _createElementVNode("ul", null, [
        _createElementVNode("li", null, "Backup completed"),
        _createElementVNode("li", null, "Invoice sent")
      ])
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a14f62dfd9c20d99b2ba735e24364532cc3b4e45df7b0f065bb1c9631642e505"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5de20a3ab63fdbf0","typeKey":"CInfiniteScroll_0e9d34","componentTag":"citry-c-infinite-scroll-3b75d624","bindings":[],"fills":[{"name":"citrySlot2303c299128fad15","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_infinite_scroll_accessibility_532961e8 = _resolveComponent("citry-infinite-scroll-accessibility-532961e8")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_infinite_scroll_accessibility_532961e8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5ed949d8341e984a.id,
      key: _ctx.$citryPrepared.calls.citryCall5ed949d8341e984a.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5677f785e655fedfbebefc274756084baf36ad9f3b9d642262f8f39b947ee3bc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5ed949d8341e984a","typeKey":"InfiniteScrollAccessibility_5c94e1","componentTag":"citry-infinite-scroll-accessibility-532961e8","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
