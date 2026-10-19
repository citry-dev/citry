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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_breadcrumbs_6414dcc2 = _resolveComponent("citry-c-breadcrumbs-6414dcc2")
  
  return (_openBlock(), _createElementBlock("section", { class: "breadcrumb-shelf" }, [
    (_openBlock(), _createBlock(_component_citry_c_breadcrumbs_6414dcc2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall28293a2e3b84876b.id,
      key: _ctx.$citryPrepared.calls.citryCall28293a2e3b84876b.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    _createElementVNode("h2", null, "The hidden life of trees"),
    _createElementVNode("p", null, "Essays on forests, roots, and the communities beneath them.")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["86984dc0283121659b224936acfac11bf7dc4ae2ac318e0a318253ff8b72ca53"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall28293a2e3b84876b","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_breadcrumbs_at_a_glance_f6c613ba = _resolveComponent("citry-breadcrumbs-at-a-glance-f6c613ba")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_breadcrumbs_at_a_glance_f6c613ba, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcadf223b8465a4e0.id,
      key: _ctx.$citryPrepared.calls.citryCallcadf223b8465a4e0.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["06327103fa11fb268cd662eecb14689f14e7e83b78534ef78cc97c7c52dadd15"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcadf223b8465a4e0","typeKey":"BreadcrumbsAtAGlance_e2821a","componentTag":"citry-breadcrumbs-at-a-glance-f6c613ba","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
