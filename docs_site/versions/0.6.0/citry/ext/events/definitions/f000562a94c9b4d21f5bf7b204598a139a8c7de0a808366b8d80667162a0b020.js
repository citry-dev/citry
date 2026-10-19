(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot39e9540beec747a3'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot39e9540beec747a3", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-dialog",
      "data-citry-dialog-surface": "",
      "aria-modal": "true",
      "data-citry-ui-part": "dialog"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", {
        class: "cui-dialog__surface",
        "data-citry-ui-part": "surface"
      }, [
        _createElementVNode("header", {
          class: "cui-dialog__header",
          "data-citry-ui-part": "header"
        }, [
          _createElementVNode("h2", _mergeProps({
            class: "cui-dialog__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs1), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f4d122daf10cdd'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f4d122daf10cdd", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            class: "cui-dialog__close",
            type: "button",
            "data-citry-dialog-close": "",
            "data-citry-dialog-built-in-close": "",
            "data-citry-ui-part": "close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, " × ")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", _mergeProps({
          class: "cui-dialog__description",
          "data-citry-ui-part": "description"
        }, _ctx.$citryPrepared.citryAttrs3), [
          (_ctx.$citryPrepared.selectedSlots['citrySlotc675106427a13a6b'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotc675106427a13a6b", { key: 2 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot4c119cf029159074'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot4c119cf029159074", { key: 3 })
            : _createCommentVNode("v-if", true)
        ]),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot200675c295c67c7c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot200675c295c67c7c", { key: 4 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ad1382c058807794e7b075e29bd732d33c53ce6e392aff616b8c0bb639c8b4fb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  
  return (_openBlock(), _createElementBlock("section", { class: "dialog-scroll-demo" }, [
    _createElementVNode("p", null, "Expedition archive"),
    _createElementVNode("h2", null, "Choose what scrolls"),
    (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle32b4bfdd7c32c4f.id,
      key: _ctx.$citryPrepared.calls.citryCalle32b4bfdd7c32c4f.key
    }, {
      ['citrySlot39e9540beec747a3']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall033e275da3882691.id,
          key: _ctx.$citryPrepared.calls.citryCall033e275da3882691.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Keep actions visible ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
        _createTextVNode(" Seven nights at the ridge ")
      ]),
      ['citrySlotc675106427a13a6b']: _withCtx(() => [
        _createTextVNode(" Body scrolling keeps this header and the actions fixed. ")
      ]),
      ['citrySlot4c119cf029159074']: _withCtx(() => [
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText12), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText13), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText14), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText15), 1 /* TEXT */)
        ]),
        _createElementVNode("article", { class: "dialog-scroll-demo__entry" }, [
          _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText16), 1 /* TEXT */),
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText17), 1 /* TEXT */)
        ])
      ]),
      ['citrySlot200675c295c67c7c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall04df3f3d2d8085af.id,
          key: _ctx.$citryPrepared.calls.citryCall04df3f3d2d8085af.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Finish reading ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a6b979eee80ae884736b502e83bdda3b10f583d549dfed0748625de4d5dfb3d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall033e275da3882691","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall04df3f3d2d8085af","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle32b4bfdd7c32c4f","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot200675c295c67c7c","localDescendants":["citryCall04df3f3d2d8085af"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCall033e275da3882691"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc675106427a13a6b","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_dialog_long_content_50bfe21b = _resolveComponent("citry-dialog-long-content-50bfe21b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_dialog_long_content_50bfe21b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1514f8e2eb6641f6.id,
      key: _ctx.$citryPrepared.calls.citryCall1514f8e2eb6641f6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["30214b08fd09fd1d63057d1097439e56e0c0c019a4d2ac9cfe12c6f3a706b175"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1514f8e2eb6641f6","typeKey":"DialogLongContent_2f4c67","componentTag":"citry-dialog-long-content-50bfe21b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
