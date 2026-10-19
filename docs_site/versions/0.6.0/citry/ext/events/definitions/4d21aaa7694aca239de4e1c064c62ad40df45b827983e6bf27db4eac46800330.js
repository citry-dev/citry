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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_accordion_item_a9553995 = _resolveComponent("citry-c-accordion-item-a9553995")
  const _component_citry_c_accordion_65b035b8 = _resolveComponent("citry-c-accordion-65b035b8")
  
  return (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall5238bc136fbcbe02.id,
    key: _ctx.$citryPrepared.calls.citryCall5238bc136fbcbe02.key
  }, {
    ['citrySlot59f911d7e7d99367']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalld70070bbe7e70491.id,
        key: _ctx.$citryPrepared.calls.citryCalld70070bbe7e70491.key
      }, {
        ['citrySlot78ab00134ec76574']: _withCtx(() => [
          _createTextVNode("Trees")
        ]),
        ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
          _createElementVNode("p", null, "Compare two trees found along the valley trail."),
          (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallcc40448392e12ddc.id,
            key: _ctx.$citryPrepared.calls.citryCallcc40448392e12ddc.key
          }, {
            ['citrySlot59f911d7e7d99367']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall9f09dae8a854f5bd.id,
                key: _ctx.$citryPrepared.calls.citryCall9f09dae8a854f5bd.key
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
                "citry-id": _ctx.$citryPrepared.calls.citryCalld18bfc2904069dd6.id,
                key: _ctx.$citryPrepared.calls.citryCalld18bfc2904069dd6.key
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
        "citry-id": _ctx.$citryPrepared.calls.citryCallc098b9f889896ca6.id,
        key: _ctx.$citryPrepared.calls.citryCallc098b9f889896ca6.key
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e724d96e412b06b7ebd2248d7b34cc9b055b6aad9c0483e1bb194f274017a82a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9f09dae8a854f5bd","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld18bfc2904069dd6","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcc40448392e12ddc","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall9f09dae8a854f5bd","citryCalld18bfc2904069dd6"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld70070bbe7e70491","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":["citryCall9f09dae8a854f5bd","citryCallcc40448392e12ddc","citryCalld18bfc2904069dd6"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc098b9f889896ca6","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5238bc136fbcbe02","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall9f09dae8a854f5bd","citryCallc098b9f889896ca6","citryCallcc40448392e12ddc","citryCalld18bfc2904069dd6","citryCalld70070bbe7e70491"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_nested_accordion_a5dbdfcd = _resolveComponent("citry-nested-accordion-a5dbdfcd")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_nested_accordion_a5dbdfcd, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall53d4770c551906f6.id,
      key: _ctx.$citryPrepared.calls.citryCall53d4770c551906f6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["35b47042d49ad43787462168a79614b5556ea14e66f3b0562564c0f935cbe50a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall53d4770c551906f6","typeKey":"NestedAccordion_7d0db4","componentTag":"citry-nested-accordion-a5dbdfcd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
