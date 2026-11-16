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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d2228cad3497a74dc3b35d99c0c8644a53abcb0dc2802d448de2b05c7736632e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  
  return (_openBlock(), _createElementBlock("section", { class: "alert-configurator" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Live configuration"),
      _createElementVNode("h2", null, "Observation status")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      intent: _ctx.intent,
      variant: _ctx.variant,
      size: _ctx.size,
      announce: _ctx.announce,
      icon: _ctx.icon,
      "citry-id": _ctx.$citryPrepared.calls.citryCalla46a98b29d79152d.id,
      key: _ctx.$citryPrepared.calls.citryCalla46a98b29d79152d.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode("Tracking update")
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode(" The guide camera is following the selected star. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["intent", "variant", "size", "announce", "icon", "citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4f77bdbfafefe8861f737f8a6f702f5aa98e3ccf12f12c821ece5e0025f94442"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla46a98b29d79152d","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[{"kind":"prop","name":":intent","value":"intent","sourceStart":149,"sourceEnd":165},{"kind":"prop","name":":variant","value":"variant","sourceStart":166,"sourceEnd":184},{"kind":"prop","name":":size","value":"size","sourceStart":185,"sourceEnd":197},{"kind":"prop","name":":announce","value":"announce","sourceStart":198,"sourceEnd":218},{"kind":"prop","name":":icon","value":"icon","sourceStart":219,"sourceEnd":231}],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_configure_alert_d848aa2e = _resolveComponent("citry-configure-alert-d848aa2e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_configure_alert_d848aa2e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall76edff8094c8890d.id,
      key: _ctx.$citryPrepared.calls.citryCall76edff8094c8890d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["dbb1bf7ef5a50032fcc9c5e3c6d5838e4ebc2a771cb387b76f76350681a98943"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall76edff8094c8890d","typeKey":"ConfigureAlert_e6e7d3","componentTag":"citry-configure-alert-d848aa2e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
