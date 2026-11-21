(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({
    class: "cui-pagination",
    "data-citry-ui-part": "pagination"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("ul", { "data-citry-ui-part": "list" }, [
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs4), _toDisplayString(_ctx.$citryPrepared.citryText3), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs5), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("span", {
          "data-citry-ui-part": "ellipsis",
          "aria-hidden": "true"
        }, "…")
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs6), _toDisplayString(_ctx.$citryPrepared.citryText5), 17 /* TEXT, FULL_PROPS */)
      ]),
      _createElementVNode("li", null, [
        _createElementVNode("button", _mergeProps({
          type: "button",
          "data-citry-ui-part": "control"
        }, _ctx.$citryPrepared.citryAttrs7), _toDisplayString(_ctx.$citryPrepared.citryText6), 17 /* TEXT, FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["94e241aaa0bce4a04e0b4396d0c6fa9921400f61e5db3c65ba2a5dedf04c1ea0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_pagination_8deb208d = _resolveComponent("citry-c-pagination-8deb208d")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createTextVNode("Plate "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.page)
      }, null, 8 /* PROPS */, ["textContent"]),
      _createTextVNode(" of 18")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_pagination_8deb208d, {
      page: _ctx.page,
      onPageChange: (next) => _ctx.page = next,
      "citry-id": _ctx.$citryPrepared.calls.citryCalla867458e15ed3370.id,
      key: _ctx.$citryPrepared.calls.citryCalla867458e15ed3370.key
    }, null, 8 /* PROPS */, ["page", "onPageChange", "citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["44b42e1784fbaacfb7e02eb8c4f13975e55eefb1655107342029201f94b8b656"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla867458e15ed3370","typeKey":"CPagination_d32cfc","componentTag":"citry-c-pagination-8deb208d","bindings":[{"kind":"prop","name":":page","value":"page","sourceStart":95,"sourceEnd":107},{"kind":"prop","name":":onPageChange","value":"(next) => page = next","sourceStart":108,"sourceEnd":145}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_pagination_ab4c2eaf = _resolveComponent("citry-controlled-pagination-ab4c2eaf")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_pagination_ab4c2eaf, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall8cb224b8843ddc36.id,
      key: _ctx.$citryPrepared.calls.citryCall8cb224b8843ddc36.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["907f460eb377c6f22a48f52cfa359e26d414447bb1f7be11cfc88d30ee89d882"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8cb224b8843ddc36","typeKey":"ControlledPagination_7d42c4","componentTag":"citry-controlled-pagination-ab4c2eaf","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
