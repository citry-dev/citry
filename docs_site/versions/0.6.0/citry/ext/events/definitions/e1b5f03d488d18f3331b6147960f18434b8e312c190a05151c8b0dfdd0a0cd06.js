(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({
    class: "cui-breadcrumbs",
    "data-citry-ui-part": "breadcrumbs"
  }, _ctx.$citryPrepared.citryAttrs0), [
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
            ? (_openBlock(), _createElementBlock("a", _mergeProps({
              key: 5,
              "data-citry-ui-part": "link"
            }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot9b92de28915c411c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot9b92de28915c411c", { key: 6 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot9b92de28915c411c'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 7 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot4ad7fc4956ae69f7'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot4ad7fc4956ae69f7", { key: 8 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot4ad7fc4956ae69f7'] === 'fallback')
            ? (_openBlock(), _createElementBlock("span", _mergeProps({
              key: 9,
              "data-citry-ui-part": "current"
            }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */))
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["41fc6ea41e439022658c64d32ec89155d1b5b61dab2c463579f2d7965fe2ffe9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9c114071be1e7825ca1e03ab6964cbc512068dd3102b61ade238b4c0841a6f32"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc7eebc4762f61125","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_route_breadcrumbs_56467869 = _resolveComponent("citry-route-breadcrumbs-56467869")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_route_breadcrumbs_56467869, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall3ad2f923fd37038d.id,
      key: _ctx.$citryPrepared.calls.citryCall3ad2f923fd37038d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["d2cf53f790b29562449f4a8c02f62542df11750642f0e3a7edd50cdd5eb955bb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3ad2f923fd37038d","typeKey":"RouteBreadcrumbs_28ef4f","componentTag":"citry-route-breadcrumbs-56467869","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
