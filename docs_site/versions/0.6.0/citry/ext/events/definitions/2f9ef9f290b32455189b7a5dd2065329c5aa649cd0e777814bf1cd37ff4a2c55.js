(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-alert",
    "data-citry-ui-part": "alert"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_openBlock(), _createElementBlock("div", {
      class: "cui-alert__indicator",
      "aria-hidden": "true",
      "data-citry-ui-part": "indicator"
    }, [
      (_openBlock(), _createElementBlock("svg", {
        class: "cui-alert__icon",
        xmlns: "http://www.w3.org/2000/svg",
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        focusable: "false",
        "aria-hidden": "true"
      }, [
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "M12 16v-4" }),
          _createElementVNode("path", { d: "M12 8h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m9 12 2 2 4-4" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs3)), [
          _createElementVNode("path", { d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" }),
          _createElementVNode("path", { d: "M12 9v4" }),
          _createElementVNode("path", { d: "M12 17h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m15 9-6 6" }),
          _createElementVNode("path", { d: "m9 9 6 6" })
        ], 16 /* FULL_PROPS */)
      ]))
    ])),
    _createElementVNode("div", {
      class: "cui-alert__content",
      "data-citry-ui-part": "content"
    }, [
      _createElementVNode("div", {
        class: "cui-alert__title",
        "data-citry-ui-part": "title"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotb882e2f6b4a5203d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotb882e2f6b4a5203d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("div", {
        class: "cui-alert__message",
        "data-citry-ui-part": "message"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot763d5ceca2695678'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot763d5ceca2695678", { key: 1 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["eff77223950856704c8dcb5011ec607ec8598be36aadc1419059773d10e2bf7a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "alert-variants",
    "aria-label": "Alert variants"
  }, [
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall8c8a0c684e79dd51.id,
      key: _ctx.$citryPrepared.calls.citryCall8c8a0c684e79dd51.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0) + " warning", 1 /* TEXT */)
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode(" High cirrus may reduce contrast on faint galaxies. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7a07f0b77750077a.id,
      key: _ctx.$citryPrepared.calls.citryCall7a07f0b77750077a.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1) + " warning", 1 /* TEXT */)
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode(" High cirrus may reduce contrast on faint galaxies. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall337fe4f7baea89ee.id,
      key: _ctx.$citryPrepared.calls.citryCall337fe4f7baea89ee.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2) + " warning", 1 /* TEXT */)
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode(" High cirrus may reduce contrast on faint galaxies. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["45b529c1e5b73b2035aea9b23d02ba3243c8b3d4586fc3ac017a8b23613c69f5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8c8a0c684e79dd51","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7a07f0b77750077a","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall337fe4f7baea89ee","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_alert_variants_c41ec3d2 = _resolveComponent("citry-alert-variants-c41ec3d2")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_alert_variants_c41ec3d2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2f182c982bdf3fae.id,
      key: _ctx.$citryPrepared.calls.citryCall2f182c982bdf3fae.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["161c9f9a606e47172b6283a1f6b233c7598b67a0e6ab65622ae96cb2494ca458"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2f182c982bdf3fae","typeKey":"AlertVariants_3d4c77","componentTag":"citry-alert-variants-c41ec3d2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
