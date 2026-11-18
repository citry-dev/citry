(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("nav", _mergeProps({
    class: "cui-breadcrumbs",
    "data-citry-ui-part": "breadcrumbs"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("ol", { "data-citry-ui-part": "list" }, [
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot698449fbf13dc16e'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot698449fbf13dc16e", { key: 0 })
          : _createCommentVNode("v-if", true),
        _createElementVNode("span", {
          "aria-hidden": "true",
          "data-citry-ui-part": "separator"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlote97ca9af649200b8'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlote97ca9af649200b8", { key: 1 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlote97ca9af649200b8'] === 'fallback')
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
              ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ])
      ]),
      _createElementVNode("li", { "data-citry-ui-part": "item" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotf81220e265c775ae'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotf81220e265c775ae", { key: 3 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["044ca2c0c0216c55b93d3ea5f63a62644d684c8710b9dfb57e22cfeb997b4e51"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_breadcrumbs_6414dcc2 = _resolveComponent("citry-c-breadcrumbs-6414dcc2")
  
  return (_openBlock(), _createBlock(_component_citry_c_breadcrumbs_6414dcc2, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall88c452b43bf3a8e6.id,
    key: _ctx.$citryPrepared.calls.citryCall88c452b43bf3a8e6.key
  }, {
    ['citrySlot698449fbf13dc16e']: _withCtx(() => [
      _createElementVNode("a", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
        _createElementVNode("span", { "aria-hidden": "true" }, "◌"),
        _createTextVNode(" " + _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */)
    ]),
    ['citrySlotf81220e265c775ae']: _withCtx(() => [
      _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */)
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f4bed1c2b12916139dc44b064c33e9296156fcebfadc99acd04fa591ad0ea123"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall88c452b43bf3a8e6","typeKey":"CBreadcrumbs_f70ab1","componentTag":"citry-c-breadcrumbs-6414dcc2","bindings":[],"fills":[{"name":"citrySlot698449fbf13dc16e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf81220e265c775ae","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_breadcrumb_item_slot_9c4f05c5 = _resolveComponent("citry-breadcrumb-item-slot-9c4f05c5")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_breadcrumb_item_slot_9c4f05c5, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall54b888ecbcc73e37.id,
      key: _ctx.$citryPrepared.calls.citryCall54b888ecbcc73e37.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8bfc9eb13204748f8e738394fb74082cbaf0b9158c1b513ca99ad2264f15a392"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall54b888ecbcc73e37","typeKey":"BreadcrumbItemSlot_8ef821","componentTag":"citry-breadcrumb-item-slot-9c4f05c5","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
