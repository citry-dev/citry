(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-accordion__item",
    "data-citry-accordion-item": "",
    "data-citry-ui-part": "accordion-item"
  }, _ctx.$citryPrepared.citryAttrs0, { key: _ctx.$citryPrepared.citryKey0 }), [
    _createElementVNode("div", {
      class: "cui-accordion__header",
      "data-citry-ui-part": "accordion-header"
    }, [
      _createElementVNode("citry-dynamic-012e9eed7ef89709", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
        _createElementVNode("button", _mergeProps({
          class: "cui-accordion__trigger",
          type: "button",
          "data-citry-accordion-trigger": "",
          "data-citry-ui-part": "accordion-trigger"
        }, _ctx.$citryPrepared.citryAttrs2), [
          _createElementVNode("span", {
            class: "cui-accordion__title",
            "data-citry-ui-part": "accordion-title"
          }, [
            (_ctx.$citryPrepared.selectedSlots['citrySlot78ab00134ec76574'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot78ab00134ec76574", { key: _ctx.$citryPrepared.slotKeys['citrySlot78ab00134ec76574'], key: _ctx.$citryPrepared.slotKeys['citrySlot78ab00134ec76574'] })
              : _createCommentVNode("v-if", true)
          ]),
          (_openBlock(), _createElementBlock("span", {
            class: "cui-accordion__indicator",
            "aria-hidden": "true",
            "data-citry-ui-part": "accordion-indicator"
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
      class: "cui-accordion__panel",
      "data-citry-accordion-panel": "",
      "data-citry-ui-part": "accordion-panel"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("div", {
        class: "cui-accordion__body",
        "data-citry-ui-part": "accordion-body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotd1ab786a8719fbb4'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotd1ab786a8719fbb4", { key: _ctx.$citryPrepared.slotKeys['citrySlotd1ab786a8719fbb4'], key: _ctx.$citryPrepared.slotKeys['citrySlotd1ab786a8719fbb4'] })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6175ede306327323fe82eb723a94e44e1ecee8af987044ef009723224c549241"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-012e9eed7ef89709","tag":"h3","sourceStart":245,"sourceEnd":313}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-012e9eed7ef89709","tag":"h3","sourceStart":245,"sourceEnd":313}]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-accordion",
    "data-citry-accordion-root": "",
    "data-citry-ui-part": "accordion"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot59f911d7e7d99367'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot59f911d7e7d99367", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["815f72491cab408a55ed08b1c1cc9126e410dee7b4686fb3a6176c4991ee3656"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_accordion_item_a9553995 = _resolveComponent("citry-c-accordion-item-a9553995")
  const _component_citry_c_accordion_65b035b8 = _resolveComponent("citry-c-accordion-65b035b8")
  
  return (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall76b7adfc022e2473.id,
    key: _ctx.$citryPrepared.calls.citryCall76b7adfc022e2473.key
  }, {
    ['citrySlot59f911d7e7d99367']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall66a8b2d92425ebab.id,
        key: _ctx.$citryPrepared.calls.citryCall66a8b2d92425ebab.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Trees")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createElementVNode("p", null, "Compare two trees found along the valley trail."),
          (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall5a7dd2294641f0d4.id,
            key: _ctx.$citryPrepared.calls.citryCall5a7dd2294641f0d4.key
          }, {
            ['citrySlot59f911d7e7d99367']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall337a48eb4e9a9b4e.id,
                key: _ctx.$citryPrepared.calls.citryCall337a48eb4e9a9b4e.key
              }, {
                ['citrySlot78ab00134ec76574']: _withCtx(() => [
                  _createTextVNode("Western red cedar")
                ]),
                ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
                  _createTextVNode("A long-lived tree of moist lowland forests.")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCallc5f73e11150a1f24.id,
                key: _ctx.$citryPrepared.calls.citryCallc5f73e11150a1f24.key
              }, {
                ['citrySlot78ab00134ec76574']: _withCtx(() => [
                  _createTextVNode("Bigleaf maple")
                ]),
                ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
                  _createTextVNode("Broad leaves support hanging gardens of moss.")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalla7231b373a443502.id,
        key: _ctx.$citryPrepared.calls.citryCalla7231b373a443502.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Wildflowers")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode("Trillium and violets bloom before the canopy closes.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["22ac8f7780d4e8e3ee4d092f9771dea3f8667c8002a956cdf406c9d2d5272e57"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall337a48eb4e9a9b4e","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc5f73e11150a1f24","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5a7dd2294641f0d4","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall337a48eb4e9a9b4e","citryCallc5f73e11150a1f24"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall66a8b2d92425ebab","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":["citryCall337a48eb4e9a9b4e","citryCall5a7dd2294641f0d4","citryCallc5f73e11150a1f24"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla7231b373a443502","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall76b7adfc022e2473","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall337a48eb4e9a9b4e","citryCall5a7dd2294641f0d4","citryCall66a8b2d92425ebab","citryCalla7231b373a443502","citryCallc5f73e11150a1f24"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_nested_accordion_5eccf4de = _resolveComponent("citry-nested-accordion-5eccf4de")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_nested_accordion_5eccf4de, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall660b3f4f45f86d0e.id,
      key: _ctx.$citryPrepared.calls.citryCall660b3f4f45f86d0e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["45b09f812027bc2de4b21c8cdb48874b825d90d88b82c022daf84ececc5fe3c7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall660b3f4f45f86d0e","typeKey":"NestedAccordion_34415b","componentTag":"citry-nested-accordion-5eccf4de","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
