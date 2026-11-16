(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    ref: "root",
    class: "cui-infinite-scroll",
    "data-citry-ui-part": "infinite-scroll"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "content" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6eb775ceb37ea393'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6eb775ceb37ea393", { key: 0 })
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
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */)
    ]),
    _createElementVNode("button", _mergeProps({
      "data-citry-infinite-scroll-action": "",
      "data-citry-ui-part": "action"
    }, _ctx.$citryPrepared.citryAttrs5), [
      _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs6)), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      "data-citry-infinite-scroll-sentinel": "",
      "data-citry-ui-part": "sentinel",
      "aria-hidden": "true"
    })
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a6a100031c51566828629c8de518acc858b7238f8a8b25b01a1f5f5a9b645b75"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, renderList: _renderList, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_infinite_scroll_3b75d624 = _resolveComponent("citry-c-infinite-scroll-3b75d624")
  
  return (_openBlock(), _createElementBlock("section", null, [
    (_openBlock(), _createBlock(_component_citry_c_infinite_scroll_3b75d624, {
      loading: _ctx.loading,
      error: _ctx.error,
      hasMore: _ctx.hasMore,
      onLoadMore: _ctx.retryPage,
      "citry-id": _ctx.$citryPrepared.calls.citryCall02dca7fd4edcd01e.id,
      key: _ctx.$citryPrepared.calls.citryCall02dca7fd4edcd01e.key
    }, {
      ['citrySlot6eb775ceb37ea393']: _withCtx(() => [
        _createElementVNode("ul", null, [
          _createElementVNode("li", null, "Order #1042"),
          _createElementVNode("li", null, "Order #1041"),
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.recoveredOrders, (order) => {
            return (_openBlock(), _createElementBlock("li", {
              key: order.id,
              textContent: _toDisplayString(order.label)
            }, null, 8 /* PROPS */, ["textContent"]))
          }), 128 /* KEYED_FRAGMENT */))
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loading", "error", "hasMore", "onLoadMore", "citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.recovered ? 'Orders recovered' : 'Last request failed')
    }, " Last request failed ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bb8ec62420c323ab88bcdb7f35c745b1b4b6f9db286ff54f506eca175ae9fde4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall02dca7fd4edcd01e","typeKey":"CInfiniteScroll_0e9d34","componentTag":"citry-c-infinite-scroll-3b75d624","bindings":[{"kind":"prop","name":":loading","value":"loading","sourceStart":47,"sourceEnd":65},{"kind":"prop","name":":error","value":"error","sourceStart":66,"sourceEnd":80},{"kind":"prop","name":":hasMore","value":"hasMore","sourceStart":81,"sourceEnd":99},{"kind":"prop","name":":onLoadMore","value":"retryPage","sourceStart":100,"sourceEnd":123}],"fills":[{"name":"citrySlot6eb775ceb37ea393","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_infinite_scroll_error_retry_c1b5d771 = _resolveComponent("citry-infinite-scroll-error-retry-c1b5d771")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_infinite_scroll_error_retry_c1b5d771, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall737f08c14dd669b1.id,
      key: _ctx.$citryPrepared.calls.citryCall737f08c14dd669b1.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["475f3d8a4c9bce0afa1940f7875ecf3a9363a44d189767ba21d5afc89de3f3d1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall737f08c14dd669b1","typeKey":"InfiniteScrollErrorRetry_21ea0f","componentTag":"citry-infinite-scroll-error-retry-c1b5d771","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
