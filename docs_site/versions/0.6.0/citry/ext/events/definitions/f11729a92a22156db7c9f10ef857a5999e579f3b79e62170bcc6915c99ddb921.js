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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_alert_dialog_64bb695e = _resolveComponent("citry-c-alert-dialog-64bb695e")
  
  return (_openBlock(), _createElementBlock("section", null, [
    (_openBlock(), _createBlock(_component_citry_c_alert_dialog_64bb695e, {
      open: _ctx.open,
      onOpenChange: (next, detail) => {
        if (detail.returnValue === 'action') {
          _ctx.pending = true;
          _ctx.result = 'Archiving...';
          window.setTimeout(() => {
            _ctx.pending = false;
            _ctx.open = false;
            _ctx.result = 'Record archived';
          }, 500);
        } else {
          _ctx.open = next;
          if (!next) _ctx.result = 'Archive cancelled';
        }
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCall536ae14c01e34f31.id,
      key: _ctx.$citryPrepared.calls.citryCall536ae14c01e34f31.key
    }, {
      ['citrySlot42f817a9b661d76d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld3a4920a1e072974.id,
          key: _ctx.$citryPrepared.calls.citryCalld3a4920a1e072974.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Archive record")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySloteeba92f5034338ea']: _withCtx(() => [
        _createTextVNode("Archive this record?")
      ]),
      ['citrySlotf9840b7f99816205']: _withCtx(() => [
        _createTextVNode("It will leave the active workspace.")
      ]),
      ['citrySlotb6ef7dbbd1a6e6b1']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          disabled: _ctx.pending,
          "citry-id": _ctx.$citryPrepared.calls.citryCalld69eb1ba04a8fc66.id,
          key: _ctx.$citryPrepared.calls.citryCalld69eb1ba04a8fc66.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Cancel")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["disabled", "citry-id"]))
      ]),
      ['citrySlot9eb3d4d1b38eeeef']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          loading: _ctx.pending,
          "citry-id": _ctx.$citryPrepared.calls.citryCall3e3bb2fb1cc284fa.id,
          key: _ctx.$citryPrepared.calls.citryCall3e3bb2fb1cc284fa.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Archive")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loading", "citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "citry-id"])),
    _createElementVNode("p", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.result)
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1cfc8231e62019287ad9b642b046d5deeb358183cd34be676dd1322c7b86d815"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld3a4920a1e072974","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld69eb1ba04a8fc66","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"prop","name":":disabled","value":"pending","sourceStart":1143,"sourceEnd":1162}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3e3bb2fb1cc284fa","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"prop","name":":loading","value":"pending","sourceStart":1468,"sourceEnd":1486}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall536ae14c01e34f31","typeKey":"CAlertDialog_4d9fc7","componentTag":"citry-c-alert-dialog-64bb695e","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":44,"sourceEnd":56},{"kind":"prop","name":":onOpenChange","value":"(next, detail) => {\n        if (detail.returnValue === 'action') {\n          pending = true;\n          result = 'Archiving...';\n          window.setTimeout(() => {\n            pending = false;\n            open = false;\n            result = 'Record archived';\n          }, 500);\n        } else {\n          open = next;\n          if (!next) result = 'Archive cancelled';\n        }\n      }","sourceStart":57,"sourceEnd":459}],"fills":[{"name":"citrySlot42f817a9b661d76d","localDescendants":["citryCalld3a4920a1e072974"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9eb3d4d1b38eeeef","localDescendants":["citryCall3e3bb2fb1cc284fa"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb6ef7dbbd1a6e6b1","localDescendants":["citryCalld69eb1ba04a8fc66"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySloteeba92f5034338ea","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf9840b7f99816205","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_archive_b2385e58 = _resolveComponent("citry-controlled-archive-b2385e58")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_archive_b2385e58, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcca127dd3fc258c0.id,
      key: _ctx.$citryPrepared.calls.citryCallcca127dd3fc258c0.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c41005692e822671c6ea8a0b660bdc970a119c76040924a5a9e99f022a9961bd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcca127dd3fc258c0","typeKey":"ControlledArchive_bce472","componentTag":"citry-controlled-archive-b2385e58","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
