(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({
    class: "cui-breadcrumbs",
    "data-citry-ui-part": "breadcrumbs"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("ol", { "data-citry-ui-part": "list" }, [
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot19e8dfd817747f22'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot19e8dfd817747f22", { key: 0 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot19e8dfd817747f22'] === 'fallback')
            ? (_openBlock(), _createElementBlock("a", _mergeProps({
              key: 1,
              "data-citry-ui-part": "link"
            }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlote97ca9af649200b8'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlote97ca9af649200b8", { key: 2 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlote97ca9af649200b8'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 3 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot62522ceb7cf5033a'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot62522ceb7cf5033a", { key: 4 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot62522ceb7cf5033a'] === 'fallback')
            ? (_openBlock(), _createElementBlock("a", _mergeProps({
              key: 5,
              "data-citry-ui-part": "link"
            }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot2ac8f43d3176ce11'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot2ac8f43d3176ce11", { key: 6 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot2ac8f43d3176ce11'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 7 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot704511a3138aea09'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot704511a3138aea09", { key: 8 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot704511a3138aea09'] === 'fallback')
            ? (_openBlock(), _createElementBlock("span", _mergeProps({
              key: 9,
              "data-citry-ui-part": "current"
            }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d737d9a6196291183ef0429823dc73aa3deadb86907fd93a2d18e150ffac8f9c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_breadcrumbs_6414dcc2 = _resolveComponent("citry-c-breadcrumbs-6414dcc2")
  
  return (_openBlock(), _createBlock(_component_citry_c_breadcrumbs_6414dcc2, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall11a0988ecc586dcc.id,
    key: _ctx.$citryPrepared.calls.citryCall11a0988ecc586dcc.key
  }, null, 8 /* PROPS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5c2a2e09ecda5f103a74a4ef1c4372de86316668eaa37e81a20afca52d5c4795"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall11a0988ecc586dcc","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_basic_breadcrumbs_cc822759 = _resolveComponent("citry-basic-breadcrumbs-cc822759")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_basic_breadcrumbs_cc822759, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall77b3b7ba1b8f5355.id,
      key: _ctx.$citryPrepared.calls.citryCall77b3b7ba1b8f5355.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["92a317bfd0e45d5f6b23ce6e4428e10c47b525d4bd6b65164707e7b10975518e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall77b3b7ba1b8f5355","typeKey":"BasicBreadcrumbs_dd8e73","componentTag":"citry-basic-breadcrumbs-cc822759","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
