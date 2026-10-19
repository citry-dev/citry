(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    ref: "root",
    class: "cui-infinite-scroll",
    "data-citry-ui-part": "infinite-scroll"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "content" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotfd58e19eb090171e'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotfd58e19eb090171e", { key: 0 })
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["648df6df094fb3dc6d649f78d280cedeb37d9d2fb8ca10066b44a9abb3a6a49d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        "citry-id": _ctx.$citryPrepared.calls.citryCall0c307ae4e1d7aada.id,
        key: _ctx.$citryPrepared.calls.citryCall0c307ae4e1d7aada.key
      }, {
        ['citrySlotfd58e19eb090171e']: _withCtx(() => [
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f5364da536d969902430e037053a4758f95a8a6210d9d1f15b29fb3bc65e2f98"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0c307ae4e1d7aada","typeKey":"CInfiniteScroll_0e9d34","componentTag":"citry-c-infinite-scroll-3b75d624","bindings":[{"kind":"prop","name":":loading","value":"loading","sourceStart":74,"sourceEnd":92},{"kind":"prop","name":":hasMore","value":"hasMore","sourceStart":93,"sourceEnd":111},{"kind":"prop","name":":onLoadMore","value":"loadNextPage","sourceStart":112,"sourceEnd":138}],"fills":[{"name":"citrySlotfd58e19eb090171e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_infinite_scroll_at_a_glance_f282c8c7 = _resolveComponent("citry-infinite-scroll-at-a-glance-f282c8c7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_infinite_scroll_at_a_glance_f282c8c7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1066e6187ce44365.id,
      key: _ctx.$citryPrepared.calls.citryCall1066e6187ce44365.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["7c835048e433c8c4ea88db57ac28234db5f219c77aadcf1c9dba0c6d6835124f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1066e6187ce44365","typeKey":"InfiniteScrollAtAGlance_87bd04","componentTag":"citry-infinite-scroll-at-a-glance-f282c8c7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
