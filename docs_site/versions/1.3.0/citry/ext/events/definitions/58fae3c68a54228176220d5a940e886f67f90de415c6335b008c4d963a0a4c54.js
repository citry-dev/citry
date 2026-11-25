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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_accordion_item_a9553995 = _resolveComponent("citry-c-accordion-item-a9553995")
  const _component_citry_c_accordion_65b035b8 = _resolveComponent("citry-c-accordion-65b035b8")
  
  return (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall07927a3af7b78ff1.id,
    key: _ctx.$citryPrepared.calls.citryCall07927a3af7b78ff1.key
  }, {
    ['citrySlot59f911d7e7d99367']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf316fc0266b831c1.id,
        key: _ctx.$citryPrepared.calls.citryCallf316fc0266b831c1.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Fern loop")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode("Open from dawn until dusk.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1424aa368cc5f477.id,
        key: _ctx.$citryPrepared.calls.citryCall1424aa368cc5f477.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Cedar crossing — temporarily closed")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode("High water has covered the footbridge.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7f8c71b27b3cd3ed.id,
        key: _ctx.$citryPrepared.calls.citryCall7f8c71b27b3cd3ed.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Wetland boardwalk")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode("A level route through reeds and alder groves.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["945c54a860a403e3d0704644a695e8cbdb2ec8457aa98cf11ddbded5aceb8939"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf316fc0266b831c1","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1424aa368cc5f477","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7f8c71b27b3cd3ed","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall07927a3af7b78ff1","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall1424aa368cc5f477","citryCall7f8c71b27b3cd3ed","citryCallf316fc0266b831c1"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_disabled_items_818ad1f9 = _resolveComponent("citry-disabled-items-818ad1f9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_disabled_items_818ad1f9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall66466987d220d209.id,
      key: _ctx.$citryPrepared.calls.citryCall66466987d220d209.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c3d07c34dbf124dc0413dec59e8bd315340a556931fb0dd027d1ab2e50e671ee"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall66466987d220d209","typeKey":"DisabledItems_6f7a3e","componentTag":"citry-disabled-items-818ad1f9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
