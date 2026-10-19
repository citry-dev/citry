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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "alert-glance",
    "aria-label": "Observatory alerts"
  }, [
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallbb447224c35b5407.id,
      key: _ctx.$citryPrepared.calls.citryCallbb447224c35b5407.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode("Meteor shower tonight")
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode("Peak activity begins near 23:10.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6af4d63a580f05bf.id,
      key: _ctx.$citryPrepared.calls.citryCall6af4d63a580f05bf.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode("Telescope aligned")
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode("Tracking error is below 0.2 arcseconds.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5294218443523d97.id,
      key: _ctx.$citryPrepared.calls.citryCall5294218443523d97.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode("Cloud bank approaching")
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode("The western horizon may close after midnight.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall25b4dfccc8b91c21.id,
      key: _ctx.$citryPrepared.calls.citryCall25b4dfccc8b91c21.key
    }, {
      ['citrySlotb882e2f6b4a5203d']: _withCtx(() => [
        _createTextVNode("Camera link lost")
      ]),
      ['citrySlot763d5ceca2695678']: _withCtx(() => [
        _createTextVNode("Reconnect before starting the next exposure.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["013d2ac260a77ef38b07307131ecd72f71848b4725610e03c605163cb8a10332"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbb447224c35b5407","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6af4d63a580f05bf","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5294218443523d97","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall25b4dfccc8b91c21","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlot763d5ceca2695678","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb882e2f6b4a5203d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_alert_at_a_glance_9cf3c2a1 = _resolveComponent("citry-alert-at-a-glance-9cf3c2a1")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_alert_at_a_glance_9cf3c2a1, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalled24bc76e71cdb51.id,
      key: _ctx.$citryPrepared.calls.citryCalled24bc76e71cdb51.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fa7d826c5bfcbf7a2168f87c2cd1c861f93aa416ae0f2a425067a8efceab2652"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalled24bc76e71cdb51","typeKey":"AlertAtAGlance_4a1678","componentTag":"citry-alert-at-a-glance-9cf3c2a1","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
