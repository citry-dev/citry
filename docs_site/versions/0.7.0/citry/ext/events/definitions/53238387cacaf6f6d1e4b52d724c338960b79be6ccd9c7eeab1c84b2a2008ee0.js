(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    ref: "root",
    class: "cui-infinite-scroll",
    "data-citry-ui-part": "infinite-scroll"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "content" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlota49bdebde638cd9f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlota49bdebde638cd9f", { key: 0 })
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
window.__citryRuntimeDefinitions["189f95401a522b858e1449b3ec50fbb4df39f3c289763918f4c5613dd63f1ae9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, renderList: _renderList, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_infinite_scroll_3b75d624 = _resolveComponent("citry-c-infinite-scroll-3b75d624")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("form", {
      onSubmit: _withModifiers(() => {}, ["prevent"])
    }, [
      (_openBlock(), _createBlock(_component_citry_c_infinite_scroll_3b75d624, {
        loading: _ctx.loading,
        hasMore: _ctx.hasMore,
        onLoadMore: _ctx.loadNextPage,
        "citry-id": _ctx.$citryPrepared.calls.citryCallb30104e15a4596d5.id,
        key: _ctx.$citryPrepared.calls.citryCallb30104e15a4596d5.key
      }, {
        ['citrySlota49bdebde638cd9f']: _withCtx(() => [
          _createElementVNode("ol", null, [
            _createElementVNode("li", null, "Created the project"),
            _createElementVNode("li", null, "Invited the design team"),
            _createElementVNode("li", null, "Published the brief"),
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.moreActivities, (activity) => {
              return (_openBlock(), _createElementBlock("li", {
                key: activity.id,
                textContent: _toDisplayString(activity.label)
              }, null, 8 /* PROPS */, ["textContent"]))
            }), 128 /* KEYED_FRAGMENT */))
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loading", "hasMore", "onLoadMore", "citry-id"]))
    ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(`Loaded ${3 + _ctx.moreActivities.length} activities`)
    }, " Loaded 3 activities ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ed4d9c671a84752aea622f53203bd15ad6ceb48868f46d69c711d4a60213bff6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb30104e15a4596d5","typeKey":"CInfiniteScroll_0e9d34","componentTag":"citry-c-infinite-scroll-3b75d624","bindings":[{"kind":"prop","name":":loading","value":"loading","sourceStart":74,"sourceEnd":92},{"kind":"prop","name":":hasMore","value":"hasMore","sourceStart":93,"sourceEnd":111},{"kind":"prop","name":":onLoadMore","value":"loadNextPage","sourceStart":112,"sourceEnd":138}],"fills":[{"name":"citrySlota49bdebde638cd9f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_infinite_scroll_at_a_glance_9592177b = _resolveComponent("citry-infinite-scroll-at-a-glance-9592177b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_infinite_scroll_at_a_glance_9592177b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall998a091422a561a6.id,
      key: _ctx.$citryPrepared.calls.citryCall998a091422a561a6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["850dc363dc1da7a44c9e5652113898b9e64c109a5eb28869609fc9c6d81126ad"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall998a091422a561a6","typeKey":"InfiniteScrollAtAGlance_a97e86","componentTag":"citry-infinite-scroll-at-a-glance-9592177b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
