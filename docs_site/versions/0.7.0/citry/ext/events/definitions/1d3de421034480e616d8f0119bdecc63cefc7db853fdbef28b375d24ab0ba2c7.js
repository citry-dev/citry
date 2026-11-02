(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    ref: "root",
    class: "cui-infinite-scroll",
    "data-citry-ui-part": "infinite-scroll"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "content" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot27ae4b13e6baff43'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot27ae4b13e6baff43", { key: 0 })
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
window.__citryRuntimeDefinitions["79d034b4b1f97f41ce1392f9b68c522d77d38063902bff9b7f66f4ea0839bf88"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createTextVNode: _createTextVNode, renderList: _renderList, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_infinite_scroll_3b75d624 = _resolveComponent("citry-c-infinite-scroll-3b75d624")
  
  return (_openBlock(), _createElementBlock("form", {
    onSubmit: _withModifiers($event => (_ctx.loadServerPage($event)), ["prevent"])
  }, [
    _createElementVNode("label", null, [
      _createTextVNode("Search query "),
      _createElementVNode("input", {
        name: "query",
        required: ""
      })
    ]),
    (_openBlock(), _createBlock(_component_citry_c_infinite_scroll_3b75d624, {
      loading: _ctx.loading,
      hasMore: _ctx.hasMore,
      "citry-id": _ctx.$citryPrepared.calls.citryCall10fbf7f44930518d.id,
      key: _ctx.$citryPrepared.calls.citryCall10fbf7f44930518d.key
    }, {
      ['citrySlot27ae4b13e6baff43']: _withCtx(() => [
        _createElementVNode("ol", null, [
          _createElementVNode("li", null, "Camera body comparison"),
          _createElementVNode("li", null, "Lens mount guide"),
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.moreResults, (result) => {
            return (_openBlock(), _createElementBlock("li", {
              key: result.id,
              textContent: _toDisplayString(result.label)
            }, null, 8 /* PROPS */, ["textContent"]))
          }), 128 /* KEYED_FRAGMENT */))
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loading", "hasMore", "citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.acceptedAction)
    }, "Waiting for a named action", 8 /* PROPS */, ["textContent"])
  ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["00abef69363b73829151afb8ccb2d75129583c632b6f98029b05f9bbb9913852"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall10fbf7f44930518d","typeKey":"CInfiniteScroll_0e9d34","componentTag":"citry-c-infinite-scroll-3b75d624","bindings":[{"kind":"prop","name":":loading","value":"loading","sourceStart":146,"sourceEnd":164},{"kind":"prop","name":":hasMore","value":"hasMore","sourceStart":165,"sourceEnd":183}],"fills":[{"name":"citrySlot27ae4b13e6baff43","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_infinite_scroll_server_action_a288b678 = _resolveComponent("citry-infinite-scroll-server-action-a288b678")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_infinite_scroll_server_action_a288b678, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfafb92770ba784d4.id,
      key: _ctx.$citryPrepared.calls.citryCallfafb92770ba784d4.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2aa7f1b42b1e4587a712def728afb7cfde10647d532d4ae4c6d0bff399861580"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfafb92770ba784d4","typeKey":"InfiniteScrollServerAction_c9a00d","componentTag":"citry-infinite-scroll-server-action-a288b678","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
