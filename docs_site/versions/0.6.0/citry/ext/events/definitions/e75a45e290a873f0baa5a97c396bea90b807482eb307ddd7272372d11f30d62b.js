(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-disclosure",
    "data-citry-disclosure-root": "",
    "data-citry-ui-part": "disclosure"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-disclosure__header",
      "data-citry-ui-part": "disclosure-header"
    }, [
      _createElementVNode("citry-dynamic-f4170320eb7443cf", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
        _createElementVNode("button", _mergeProps({
          class: "cui-disclosure__trigger",
          type: "button",
          "data-citry-disclosure-trigger": "",
          "data-citry-ui-part": "disclosure-trigger"
        }, _ctx.$citryPrepared.citryAttrs2), [
          _createElementVNode("span", {
            class: "cui-disclosure__title",
            "data-citry-ui-part": "disclosure-title"
          }, [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e2ca619259b58f7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e2ca619259b58f7", { key: 0 })
              : _createCommentVNode("v-if", true)
          ]),
          (_openBlock(), _createElementBlock("span", {
            class: "cui-disclosure__indicator",
            "aria-hidden": "true",
            "data-citry-ui-part": "disclosure-indicator"
          }, [
            (_openBlock(), _createElementBlock("svg", {
              xmlns: "http://www.w3.org/2000/svg",
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              focusable: "false",
              "aria-hidden": "true"
            }, [
              _createElementVNode("path", { d: "m6 9 6 6 6-6" })
            ]))
          ]))
        ], 16 /* FULL_PROPS */)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-disclosure__panel",
      "data-citry-disclosure-panel": "",
      "data-citry-ui-part": "disclosure-panel"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("div", {
        class: "cui-disclosure__body",
        "data-citry-ui-part": "disclosure-body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot24b36c89b7f055eb'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot24b36c89b7f055eb", { key: 1 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e877023af7586584d9b0445405f248eed3c20ad2f1b822c9755e2273f344c49d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_disclosure_63b10531 = _resolveComponent("citry-c-disclosure-63b10531")
  
  return (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallce4f46400d65a8cf.id,
    key: _ctx.$citryPrepared.calls.citryCallce4f46400d65a8cf.key
  }, {
    ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
      _createTextVNode("System requirements")
    ]),
    ['citrySlot24b36c89b7f055eb']: _withCtx(() => [
      _createElementVNode("p", null, "Python 3.13 or newer and 512 MB of available storage.")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["55501aabfead09dbdfa9d75051588d2aab396ff3fb70e5033433184066bdae78"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallce4f46400d65a8cf","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot24b36c89b7f055eb","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_disclosure_at_a_glance_0ab8ad9f = _resolveComponent("citry-disclosure-at-a-glance-0ab8ad9f")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_disclosure_at_a_glance_0ab8ad9f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0a3e5f9cf3dff793.id,
      key: _ctx.$citryPrepared.calls.citryCall0a3e5f9cf3dff793.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6b34e843908765e6c7b0dfc36e2d5781c6b66e64ac6f21de3c5949614555679f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0a3e5f9cf3dff793","typeKey":"DisclosureAtAGlance_652c1d","componentTag":"citry-disclosure-at-a-glance-0ab8ad9f","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
