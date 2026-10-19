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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["21783d71401b0a8841e3e0add995b40bf0ba6b79f604637d90055359597c6d13"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-012e9eed7ef89709","tag":"h3","sourceStart":245,"sourceEnd":313}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f2dcfd4b3e4649f13e06bc65b89531a9bd0c33fdc90ed6a2d3daf02d65d9921b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_accordion_item_a9553995 = _resolveComponent("citry-c-accordion-item-a9553995")
  const _component_citry_c_accordion_65b035b8 = _resolveComponent("citry-c-accordion-65b035b8")
  
  return (_openBlock(), _createElementBlock("section", { class: "controlled-accordion" }, [
    _createElementVNode("p", { "aria-live": "polite" }, [
      _createTextVNode(" Open section: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.selected ?? 'none')
      }, "lichen", 8 /* PROPS */, ["textContent"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
      value: _ctx.selected,
      onValueChange: (value) => _ctx.selected = value,
      "citry-id": _ctx.$citryPrepared.calls.citryCall6ef04d617a597735.id,
      key: _ctx.$citryPrepared.calls.citryCall6ef04d617a597735.key
    }, {
      ['citrySlot59f911d7e7d99367']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall9d98ff26a844c1ce.id,
          key: _ctx.$citryPrepared.calls.citryCall9d98ff26a844c1ce.key
        }, {
          ['citrySlot78ab00134ec76574']: _withCtx(() => [
            _createTextVNode("Lichen")
          ]),
          ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
            _createTextVNode("A partnership between fungi and algae.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallbd5b8b01023be5ad.id,
          key: _ctx.$citryPrepared.calls.citryCallbd5b8b01023be5ad.key
        }, {
          ['citrySlot78ab00134ec76574']: _withCtx(() => [
            _createTextVNode("Mushrooms")
          ]),
          ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
            _createTextVNode("Temporary fruiting bodies of hidden fungal networks.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall4551dc59fb1d158b.id,
          key: _ctx.$citryPrepared.calls.citryCall4551dc59fb1d158b.key
        }, {
          ['citrySlot78ab00134ec76574']: _withCtx(() => [
            _createTextVNode("Ferns")
          ]),
          ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
            _createTextVNode("Ancient plants that reproduce through spores.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["value", "onValueChange", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f5cdde034c47e53b2d8f39895273e968a75499defd90ee2a9dc7b30858935616"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9d98ff26a844c1ce","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbd5b8b01023be5ad","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4551dc59fb1d158b","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6ef04d617a597735","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[{"kind":"prop","name":":value","value":"selected","sourceStart":172,"sourceEnd":189},{"kind":"prop","name":":onValueChange","value":"(value) => selected = value","sourceStart":190,"sourceEnd":234}],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall4551dc59fb1d158b","citryCall9d98ff26a844c1ce","citryCallbd5b8b01023be5ad"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_accordion_dfe1a650 = _resolveComponent("citry-controlled-accordion-dfe1a650")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_accordion_dfe1a650, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall90320e5fbb6698b2.id,
      key: _ctx.$citryPrepared.calls.citryCall90320e5fbb6698b2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8f8c5a69befafab83f283cbdaa8f62787205a0dc0e3b5aef730b6df20cb98b89"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall90320e5fbb6698b2","typeKey":"ControlledAccordion_76c653","componentTag":"citry-controlled-accordion-dfe1a650","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
