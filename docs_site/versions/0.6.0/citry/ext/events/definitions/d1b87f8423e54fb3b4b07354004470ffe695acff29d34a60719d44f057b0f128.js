(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({
    class: "cui-breadcrumbs",
    "data-citry-ui-part": "breadcrumbs"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("ol", { "data-citry-ui-part": "list" }, [
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot379f1075e04c84e8'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot379f1075e04c84e8", { key: 0 })
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot8398c9ba12770baa'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot8398c9ba12770baa", { key: 1 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot8398c9ba12770baa'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlote26d24d58b172e31'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlote26d24d58b172e31", { key: 3 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a773ffca720323f3bfddf2f150fff661c0a43f4a1acfea56372a4e8cdea6565c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_breadcrumbs_6414dcc2 = _resolveComponent("citry-c-breadcrumbs-6414dcc2")
  
  return (_openBlock(), _createBlock(_component_citry_c_breadcrumbs_6414dcc2, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall88c452b43bf3a8e6.id,
    key: _ctx.$citryPrepared.calls.citryCall88c452b43bf3a8e6.key
  }, {
    ['citrySlot379f1075e04c84e8']: _withCtx(() => [
      _createElementVNode("a", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
        _createElementVNode("span", { "aria-hidden": "true" }, "◌"),
        _createTextVNode(" " + _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */)
    ]),
    ['citrySlote26d24d58b172e31']: _withCtx(() => [
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */)
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5e207cc6a103cc9be2c1b5b8658b4ebb4cc7b085108373271341700f7117444d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall88c452b43bf3a8e6","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[],"fills":[{"name":"citrySlot379f1075e04c84e8","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote26d24d58b172e31","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_breadcrumb_item_slot_6b23a51e = _resolveComponent("citry-breadcrumb-item-slot-6b23a51e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_breadcrumb_item_slot_6b23a51e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall03053ee0886aef45.id,
      key: _ctx.$citryPrepared.calls.citryCall03053ee0886aef45.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["56b764e2aec34043d25ee5555c9c8827457f916683069d1330045467699db817"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall03053ee0886aef45","typeKey":"BreadcrumbItemSlot_a5d536","componentTag":"citry-breadcrumb-item-slot-6b23a51e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
