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
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot7b13e33c0cc31ff6'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot7b13e33c0cc31ff6", { key: 3 })
            : _createCommentVNode("v-if", true),
          (_ctx.$citryPrepared.selectedSlots['citrySlot9863a0b3c4618db6'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot9863a0b3c4618db6", { key: 4 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["21063f3f74b6e3b6d6815acc5c0e065e33ea3e40811a11b5fb718a445728e932"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_dialog_64bb695e = _resolveComponent("citry-c-alert-dialog-64bb695e")
  
  return (_openBlock(), _createBlock(_component_citry_c_alert_dialog_64bb695e, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallbf023432232010dc.id,
    key: _ctx.$citryPrepared.calls.citryCallbf023432232010dc.key
  }, {
    ['citrySlot21cd47f4d34f88de']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), "Leave editor", 16 /* FULL_PROPS */)
    ]),
    ['citrySlote1d483eaca719f83']: _withCtx(() => [
      _createTextVNode("Leave the editor?")
    ]),
    ['citrySlota955e5fc6e74cd26']: _withCtx(() => [
      _createTextVNode("Changes since the last save will be lost.")
    ]),
    ['citrySlot7b13e33c0cc31ff6']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), "Stay", 16 /* FULL_PROPS */)
    ]),
    ['citrySlot9863a0b3c4618db6']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), "Leave", 16 /* FULL_PROPS */)
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["cf7a031221836bbecc22736277ac8022338ee5d74c0b3b9fa307cc70f1853468"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbf023432232010dc","typeKey":"CAlertDialog_4d9fc7","componentTag":"citry-c-alert-dialog-64bb695e","bindings":[],"fills":[{"name":"citrySlot21cd47f4d34f88de","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot7b13e33c0cc31ff6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9863a0b3c4618db6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlota955e5fc6e74cd26","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote1d483eaca719f83","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_native_alert_buttons_3834a0d9 = _resolveComponent("citry-native-alert-buttons-3834a0d9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_native_alert_buttons_3834a0d9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7339c8134a087e7b.id,
      key: _ctx.$citryPrepared.calls.citryCall7339c8134a087e7b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3a103b4c70b72811df41448ac5124736cefb171470a6a5c39e7845d342a732e1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7339c8134a087e7b","typeKey":"NativeAlertButtons_169fae","componentTag":"citry-native-alert-buttons-3834a0d9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
