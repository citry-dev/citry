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
  
  return (_openBlock(), _createElementBlock("section", {
    class: "accordion-variants",
    "aria-label": "Accordion variants"
  }, [
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall8c8cf18b641a6d5f.id,
        key: _ctx.$citryPrepared.calls.citryCall8c8cf18b641a6d5f.key
      }, {
        ['citrySlot59f911d7e7d99367']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld7ae7b7f934f8378.id,
            key: _ctx.$citryPrepared.calls.citryCalld7ae7b7f934f8378.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Rainfall")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Frequent mist keeps the forest green.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld5684218644ed67e.id,
            key: _ctx.$citryPrepared.calls.citryCalld5684218644ed67e.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Filtered light")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Sunflecks move across the understory.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7b5ebf3616054084.id,
        key: _ctx.$citryPrepared.calls.citryCall7b5ebf3616054084.key
      }, {
        ['citrySlot59f911d7e7d99367']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall4a7e2f212d830fc6.id,
            key: _ctx.$citryPrepared.calls.citryCall4a7e2f212d830fc6.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Rainfall")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Frequent mist keeps the forest green.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall8b67e806ad6bf949.id,
            key: _ctx.$citryPrepared.calls.citryCall8b67e806ad6bf949.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Filtered light")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Sunflecks move across the understory.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1ccde3f077801fdd.id,
        key: _ctx.$citryPrepared.calls.citryCall1ccde3f077801fdd.key
      }, {
        ['citrySlot59f911d7e7d99367']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld8074f032cf4bea7.id,
            key: _ctx.$citryPrepared.calls.citryCalld8074f032cf4bea7.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Rainfall")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Frequent mist keeps the forest green.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall4895951938d1f9fd.id,
            key: _ctx.$citryPrepared.calls.citryCall4895951938d1f9fd.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Filtered light")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Sunflecks move across the understory.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
      (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall3fc2d028da4375a5.id,
        key: _ctx.$citryPrepared.calls.citryCall3fc2d028da4375a5.key
      }, {
        ['citrySlot59f911d7e7d99367']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1eb071f42ec90226.id,
            key: _ctx.$citryPrepared.calls.citryCall1eb071f42ec90226.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Rainfall")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Frequent mist keeps the forest green.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall22bc37c4b1687322.id,
            key: _ctx.$citryPrepared.calls.citryCall22bc37c4b1687322.key
          }, {
            ['citrySlot78ab00134ec76574']: _withCtx(() => [
              _createTextVNode("Filtered light")
            ]),
            ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
              _createTextVNode("Sunflecks move across the understory.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", { class: "accordion-variants__sizes" }, [
      _createElementVNode("h2", null, "Sizes"),
      _createElementVNode("div", { class: "accordion-variants__size-grid" }, [
        _createElementVNode("div", null, [
          _createElementVNode("h3", null, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
          (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallb31a7a42f4d2b74c.id,
            key: _ctx.$citryPrepared.calls.citryCallb31a7a42f4d2b74c.key
          }, {
            ['citrySlot59f911d7e7d99367']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall474baf7f0cce6f11.id,
                key: _ctx.$citryPrepared.calls.citryCall474baf7f0cce6f11.key
              }, {
                ['citrySlot78ab00134ec76574']: _withCtx(() => [
                  _createTextVNode("Moss cover")
                ]),
                ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
                  _createTextVNode("Soft ground holds overnight rain.")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _createElementVNode("div", null, [
          _createElementVNode("h3", null, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */),
          (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall2bbdf09f37ac24b6.id,
            key: _ctx.$citryPrepared.calls.citryCall2bbdf09f37ac24b6.key
          }, {
            ['citrySlot59f911d7e7d99367']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall32754ef9fe96f088.id,
                key: _ctx.$citryPrepared.calls.citryCall32754ef9fe96f088.key
              }, {
                ['citrySlot78ab00134ec76574']: _withCtx(() => [
                  _createTextVNode("Moss cover")
                ]),
                ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
                  _createTextVNode("Soft ground holds overnight rain.")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _createElementVNode("div", null, [
          _createElementVNode("h3", null, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */),
          (_openBlock(), _createBlock(_component_citry_c_accordion_65b035b8, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall19714e316fdb4dac.id,
            key: _ctx.$citryPrepared.calls.citryCall19714e316fdb4dac.key
          }, {
            ['citrySlot59f911d7e7d99367']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_accordion_item_a9553995, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall81df8e17319c628d.id,
                key: _ctx.$citryPrepared.calls.citryCall81df8e17319c628d.key
              }, {
                ['citrySlot78ab00134ec76574']: _withCtx(() => [
                  _createTextVNode("Moss cover")
                ]),
                ['citrySlotd1ab786a8719fbb4']: _withCtx(() => [
                  _createTextVNode("Soft ground holds overnight rain.")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ])
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["0bd8d53fcf36c53a60dbf99f398550e5305d2516c680e714d020cafbeb56ea04"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld7ae7b7f934f8378","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld5684218644ed67e","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8c8cf18b641a6d5f","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCalld5684218644ed67e","citryCalld7ae7b7f934f8378"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4a7e2f212d830fc6","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8b67e806ad6bf949","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7b5ebf3616054084","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall4a7e2f212d830fc6","citryCall8b67e806ad6bf949"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld8074f032cf4bea7","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4895951938d1f9fd","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1ccde3f077801fdd","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall4895951938d1f9fd","citryCalld8074f032cf4bea7"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1eb071f42ec90226","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall22bc37c4b1687322","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3fc2d028da4375a5","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall1eb071f42ec90226","citryCall22bc37c4b1687322"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall474baf7f0cce6f11","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb31a7a42f4d2b74c","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall474baf7f0cce6f11"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall32754ef9fe96f088","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2bbdf09f37ac24b6","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall32754ef9fe96f088"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall81df8e17319c628d","typeKey":"CAccordionItem_f4da52","componentTag":"citry-c-accordion-item-a9553995","bindings":[],"fills":[{"name":"citrySlot78ab00134ec76574","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd1ab786a8719fbb4","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall19714e316fdb4dac","typeKey":"CAccordion_4083eb","componentTag":"citry-c-accordion-65b035b8","bindings":[],"fills":[{"name":"citrySlot59f911d7e7d99367","localDescendants":["citryCall81df8e17319c628d"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_accordion_variants_4861c541 = _resolveComponent("citry-accordion-variants-4861c541")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_accordion_variants_4861c541, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallda905ac97d77f01d.id,
      key: _ctx.$citryPrepared.calls.citryCallda905ac97d77f01d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3d0761c819e56203e6fc03e626f104bf18458802d036c31836d00637f455d0ff"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallda905ac97d77f01d","typeKey":"AccordionVariants_a94af7","componentTag":"citry-accordion-variants-4861c541","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
