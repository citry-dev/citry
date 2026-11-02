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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot01f533d219338d4d'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot01f533d219338d4d", { key: 0 })
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot81c7ca490fc15941'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot81c7ca490fc15941", { key: 1 })
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
          (_ctx.$citryPrepared.selectedSlots['citrySlotf0252007f9ecd074'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotf0252007f9ecd074", { key: 2 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlotc18de8dd8e2a7fea'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotc18de8dd8e2a7fea", { key: 3 })
            : _createCommentVNode("v-if", true)
        ]),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot02ca7b57762cc54c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot02ca7b57762cc54c", { key: 4 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0eec404bebde2247660c971e4936ac233298c480d9ef896e6309367e16f2d7f8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      ['citrySlot01f533d219338d4d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall94894bbcdd25415a.id,
          key: _ctx.$citryPrepared.calls.citryCall94894bbcdd25415a.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Keep actions visible ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot81c7ca490fc15941']: _withCtx(() => [
        _createTextVNode(" Seven nights at the ridge ")
      ]),
      ['citrySlotf0252007f9ecd074']: _withCtx(() => [
        _createTextVNode(" Body scrolling keeps this header and the actions fixed. ")
      ]),
      ['citrySlotc18de8dd8e2a7fea']: _withCtx(() => [
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
      ['citrySlot02ca7b57762cc54c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall8e59832dccdee05d.id,
          key: _ctx.$citryPrepared.calls.citryCall8e59832dccdee05d.key
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ba5dd2a92a902bbef40df5738121ee3d1fb45394839b632374884010b505081b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall94894bbcdd25415a","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8e59832dccdee05d","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle32b4bfdd7c32c4f","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot01f533d219338d4d","localDescendants":["citryCall94894bbcdd25415a"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot02ca7b57762cc54c","localDescendants":["citryCall8e59832dccdee05d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot81c7ca490fc15941","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc18de8dd8e2a7fea","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf0252007f9ecd074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_dialog_long_content_2f4d880e = _resolveComponent("citry-dialog-long-content-2f4d880e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_dialog_long_content_2f4d880e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1cc0e3e33943feb1.id,
      key: _ctx.$citryPrepared.calls.citryCall1cc0e3e33943feb1.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5595c27f4682923c70c4b21e7f4ee75127aaa60c2f426ae61913759035518a9f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1cc0e3e33943feb1","typeKey":"DialogLongContent_49f77c","componentTag":"citry-dialog-long-content-2f4d880e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
