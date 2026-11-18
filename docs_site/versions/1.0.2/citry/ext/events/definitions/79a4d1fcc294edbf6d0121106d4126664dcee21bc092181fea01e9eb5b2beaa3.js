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
    "citry-id": _ctx.$citryPrepared.calls.citryCallc7eebc4762f61125.id,
    key: _ctx.$citryPrepared.calls.citryCallc7eebc4762f61125.key
  }, null, 8 /* PROPS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1a5eb8a091e8fcfa69bb5e1c2f183fbc230be56a33064768543386032d0bb7d5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc7eebc4762f61125","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_route_breadcrumbs_d44f7f18 = _resolveComponent("citry-route-breadcrumbs-d44f7f18")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_route_breadcrumbs_d44f7f18, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall561354a88a496efd.id,
      key: _ctx.$citryPrepared.calls.citryCall561354a88a496efd.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9e6005ae2c8d87749b3b51c4d00a2169c338f5c89438d5091a72cb034fd65ebe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall561354a88a496efd","typeKey":"RouteBreadcrumbs_1e1ed2","componentTag":"citry-route-breadcrumbs-d44f7f18","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
