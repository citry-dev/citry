(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({ "data-citry-ui-part": "breadcrumbs" }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("ol", { "data-citry-ui-part": "list" }, [
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlote0ce69ba3ff1dd8c'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlote0ce69ba3ff1dd8c", { key: 0 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlote0ce69ba3ff1dd8c'] === 'fallback')
            ? (_openBlock(), _createElementBlock("a", _mergeProps({
              key: 1,
              "data-citry-ui-part": "link"
            }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot8398c9ba12770baa'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot8398c9ba12770baa", { key: 2 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot8398c9ba12770baa'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 3 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlote75725aa501f4f54'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlote75725aa501f4f54", { key: 4 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlote75725aa501f4f54'] === 'fallback')
            ? (_openBlock(), _createElementBlock("span", _mergeProps({
              key: 5,
              "data-citry-ui-part": "current"
            }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6d4d3f86d1af12cb702ab5fd42e7cea401355f05f7b3ccc4a9fa2f43d994f5ee"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["636d062b11a040003eb688fd92440dc7e7c4ea500013b703f4444c0ac09a1862"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle6f5932df817de8b","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_custom_breadcrumbs_970525d7 = _resolveComponent("citry-custom-breadcrumbs-970525d7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_custom_breadcrumbs_970525d7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6fc59d8bce373391.id,
      key: _ctx.$citryPrepared.calls.citryCall6fc59d8bce373391.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4c9928e4606ee871ed4adee2a1ad267db1b467c9f13460cb5fb36c38cc7b1375"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6fc59d8bce373391","typeKey":"CustomBreadcrumbs_2e822f","componentTag":"citry-custom-breadcrumbs-970525d7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
