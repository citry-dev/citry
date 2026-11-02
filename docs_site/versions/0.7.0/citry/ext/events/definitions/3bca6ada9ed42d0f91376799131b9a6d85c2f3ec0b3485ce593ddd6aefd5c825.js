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
    class: "cui-dialog-host cui-alert-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot21cd47f4d34f88de'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot21cd47f4d34f88de", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-dialog cui-alert-dialog",
      role: "alertdialog",
      "aria-modal": "true",
      "data-citry-dialog-surface": "",
      "data-citry-ui-part": "alert-dialog"
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
            (_ctx.$citryPrepared.selectedSlots['citrySlote1d483eaca719f83'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlote1d483eaca719f83", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", _mergeProps({
          class: "cui-dialog__description",
          "data-citry-ui-part": "description"
        }, _ctx.$citryPrepared.citryAttrs2), [
          (_ctx.$citryPrepared.selectedSlots['citrySlota955e5fc6e74cd26'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlota955e5fc6e74cd26", { key: 2 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot383a5651b62cd541'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot383a5651b62cd541", { key: 3 })
            : _createCommentVNode("v-if", true)
        ]),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot7b13e33c0cc31ff6'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot7b13e33c0cc31ff6", { key: 4 })
            : _createCommentVNode("v-if", true),
          (_ctx.$citryPrepared.selectedSlots['citrySlot9863a0b3c4618db6'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot9863a0b3c4618db6", { key: 5 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["804522d460b26ed8311283b38b47784fcab917cad0136b154e89c4a310bfcf11"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_alert_dialog_64bb695e = _resolveComponent("citry-c-alert-dialog-64bb695e")
  
  return (_openBlock(), _createBlock(_component_citry_c_alert_dialog_64bb695e, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall912105f03b7fae39.id,
    key: _ctx.$citryPrepared.calls.citryCall912105f03b7fae39.key
  }, {
    ['citrySlot21cd47f4d34f88de']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall226b6068534eefdf.id,
        key: _ctx.$citryPrepared.calls.citryCall226b6068534eefdf.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Show sync error")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    ['citrySlote1d483eaca719f83']: _withCtx(() => [
      _createTextVNode("Changes could not be synchronized")
    ]),
    ['citrySlota955e5fc6e74cd26']: _withCtx(() => [
      _createTextVNode(" Reconnect before continuing so this draft is not overwritten. ")
    ]),
    ['citrySlot383a5651b62cd541']: _withCtx(() => [
      _createTextVNode(" Your local draft remains available in this browser. ")
    ]),
    ['citrySlot7b13e33c0cc31ff6']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6fbff26240ad561b.id,
        key: _ctx.$citryPrepared.calls.citryCall6fbff26240ad561b.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Review draft")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    ['citrySlot9863a0b3c4618db6']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallc1673184906718da.id,
        key: _ctx.$citryPrepared.calls.citryCallc1673184906718da.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Retry connection")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["61185342acfb1afe9a77888968e768705e0f044da381762101fedef566815ef0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall226b6068534eefdf","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6fbff26240ad561b","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc1673184906718da","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall912105f03b7fae39","typeKey":"CAlertDialog_4d9fc7","componentTag":"citry-c-alert-dialog-64bb695e","bindings":[],"fills":[{"name":"citrySlot21cd47f4d34f88de","localDescendants":["citryCall226b6068534eefdf"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot383a5651b62cd541","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot7b13e33c0cc31ff6","localDescendants":["citryCall6fbff26240ad561b"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9863a0b3c4618db6","localDescendants":["citryCallc1673184906718da"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlota955e5fc6e74cd26","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote1d483eaca719f83","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_blocking_error_7107ca8c = _resolveComponent("citry-blocking-error-7107ca8c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_blocking_error_7107ca8c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall98ca8b142e8973e6.id,
      key: _ctx.$citryPrepared.calls.citryCall98ca8b142e8973e6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3b2f5c6fb8c499923412d4c160259ea052ee6dd465f765f305f5ae0150e2e9e1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall98ca8b142e8973e6","typeKey":"BlockingError_f39c51","componentTag":"citry-blocking-error-7107ca8c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
