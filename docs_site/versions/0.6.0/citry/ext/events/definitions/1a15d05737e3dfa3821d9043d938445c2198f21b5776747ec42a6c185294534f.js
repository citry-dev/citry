(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host cui-alert-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot42f817a9b661d76d'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot42f817a9b661d76d", { key: 0 })
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
            (_ctx.$citryPrepared.selectedSlots['citrySloteeba92f5034338ea'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySloteeba92f5034338ea", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", _mergeProps({
          class: "cui-dialog__description",
          "data-citry-ui-part": "description"
        }, _ctx.$citryPrepared.citryAttrs2), [
          (_ctx.$citryPrepared.selectedSlots['citrySlotf9840b7f99816205'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotf9840b7f99816205", { key: 2 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlotb6ef7dbbd1a6e6b1'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotb6ef7dbbd1a6e6b1", { key: 3 })
            : _createCommentVNode("v-if", true),
          (_ctx.$citryPrepared.selectedSlots['citrySlot9eb3d4d1b38eeeef'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot9eb3d4d1b38eeeef", { key: 4 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9326fd3b41d2f791b0d1a070fd1a24d596dbc6bd7f0bd1e909b22618ae0570fb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_dialog_64bb695e = _resolveComponent("citry-c-alert-dialog-64bb695e")
  
  return (_openBlock(), _createBlock(_component_citry_c_alert_dialog_64bb695e, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallbf023432232010dc.id,
    key: _ctx.$citryPrepared.calls.citryCallbf023432232010dc.key
  }, {
    ['citrySlot42f817a9b661d76d']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), "Leave editor", 16 /* FULL_PROPS */)
    ]),
    ['citrySloteeba92f5034338ea']: _withCtx(() => [
      _createTextVNode("Leave the editor?")
    ]),
    ['citrySlotf9840b7f99816205']: _withCtx(() => [
      _createTextVNode("Changes since the last save will be lost.")
    ]),
    ['citrySlotb6ef7dbbd1a6e6b1']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), "Stay", 16 /* FULL_PROPS */)
    ]),
    ['citrySlot9eb3d4d1b38eeeef']: _withCtx(() => [
      _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), "Leave", 16 /* FULL_PROPS */)
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["82efa603ab999b58ad4cd411fbe67ba1731c244bccb74ee7e4f1f5623a59f1b7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbf023432232010dc","typeKey":"CAlertDialog_4d9fc7","componentTag":"citry-c-alert-dialog-64bb695e","bindings":[],"fills":[{"name":"citrySlot42f817a9b661d76d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9eb3d4d1b38eeeef","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb6ef7dbbd1a6e6b1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySloteeba92f5034338ea","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf9840b7f99816205","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_native_alert_buttons_984f6646 = _resolveComponent("citry-native-alert-buttons-984f6646")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_native_alert_buttons_984f6646, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall29c883580b78ae35.id,
      key: _ctx.$citryPrepared.calls.citryCall29c883580b78ae35.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["0aa3e976328a27fa519630c8690db0b9d35f80fdd888b1f3521e95ff97560dce"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall29c883580b78ae35","typeKey":"NativeAlertButtons_55970a","componentTag":"citry-native-alert-buttons-984f6646","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
