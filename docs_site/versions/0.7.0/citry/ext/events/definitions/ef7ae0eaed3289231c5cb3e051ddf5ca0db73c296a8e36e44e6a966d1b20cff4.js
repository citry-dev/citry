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
    "citry-id": _ctx.$citryPrepared.calls.citryCallfa62189b78a36d35.id,
    key: _ctx.$citryPrepared.calls.citryCallfa62189b78a36d35.key
  }, {
    ['citrySlot59f911d7e7d99367']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7f9ea1c71bad1b30.id,
        key: _ctx.$citryPrepared.calls.citryCall7f9ea1c71bad1b30.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Moss gardens")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode(" Moss retains moisture around roots and fallen logs. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6b4eee205c9ee051.id,
        key: _ctx.$citryPrepared.calls.citryCall6b4eee205c9ee051.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Cold streams")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode(" Shaded water stays cool enough for salmon and stoneflies. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall80f87e00f8942028.id,
        key: _ctx.$citryPrepared.calls.citryCall80f87e00f8942028.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Nurse logs")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createTextVNode(" Seedlings use decaying trunks as raised, nutrient-rich beds. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["260281df74fd3974746c009205ccdec2486c81baa7e881f5cbf1db62d46f511e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7f9ea1c71bad1b30","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6b4eee205c9ee051","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall80f87e00f8942028","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallfa62189b78a36d35","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall6b4eee205c9ee051","citryCall7f9ea1c71bad1b30","citryCall80f87e00f8942028"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_basic_accordion_02d61b31 = _resolveComponent("citry-basic-accordion-02d61b31")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_basic_accordion_02d61b31, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall87887d2e16311ebf.id,
      key: _ctx.$citryPrepared.calls.citryCall87887d2e16311ebf.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c122cb10293d5985168f7f4b35bfde098579981860c87ff33ac0f363c95daf61"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall87887d2e16311ebf","typeKey":"BasicAccordion_90f49f","componentTag":"citry-basic-accordion-02d61b31","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
