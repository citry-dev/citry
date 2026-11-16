(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({ "data-citry-ui-part": "breadcrumbs" }, _ctx.$citryPrepared.citryAttrs0), [
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
            ? (_openBlock(), _createElementBlock("span", _mergeProps({
              key: 5,
              "data-citry-ui-part": "current"
            }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["55f4fd796c0a5b383fb4af5fd8ef631fcb6b592e09e9e91e46f412ccf025e302"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_breadcrumbs_6414dcc2 = _resolveComponent("citry-c-breadcrumbs-6414dcc2")
  
  return (_openBlock(), _createBlock(_component_citry_c_breadcrumbs_6414dcc2, {
    "citry-id": _ctx.$citryPrepared.calls.citryCalle6f5932df817de8b.id,
    key: _ctx.$citryPrepared.calls.citryCalle6f5932df817de8b.key
  }, null, 8 /* PROPS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4f1d1c9e63527d353a7e3a4b729b35f2547f2ac4d52e2fc139f026164c6ef4c7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle6f5932df817de8b","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_custom_breadcrumbs_181dc9b6 = _resolveComponent("citry-custom-breadcrumbs-181dc9b6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_custom_breadcrumbs_181dc9b6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallc73611c74e3360d5.id,
      key: _ctx.$citryPrepared.calls.citryCallc73611c74e3360d5.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["58523a49af9c884936d650b3d0cc8b1864389dba10398e31cc006dce783159b9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc73611c74e3360d5","typeKey":"CustomBreadcrumbs_897fd5","componentTag":"citry-custom-breadcrumbs-181dc9b6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
