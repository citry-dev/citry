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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_alert_dialog_64bb695e = _resolveComponent("citry-c-alert-dialog-64bb695e")
  
  return (_openBlock(), _createBlock(_component_citry_c_alert_dialog_64bb695e, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallebf22779e640ecac.id,
    key: _ctx.$citryPrepared.calls.citryCallebf22779e640ecac.key
  }, {
    ['citrySlot21cd47f4d34f88de']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall28946b3e32edd524.id,
        key: _ctx.$citryPrepared.calls.citryCall28946b3e32edd524.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Delete project")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    ['citrySlote1d483eaca719f83']: _withCtx(() => [
      _createTextVNode("Delete this project?")
    ]),
    ['citrySlota955e5fc6e74cd26']: _withCtx(() => [
      _createTextVNode("This permanently removes all project data.")
    ]),
    ['citrySlot7b13e33c0cc31ff6']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalld28748ba57c350d8.id,
        key: _ctx.$citryPrepared.calls.citryCalld28748ba57c350d8.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Keep project")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    ['citrySlot9863a0b3c4618db6']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallc8b874e9279def47.id,
        key: _ctx.$citryPrepared.calls.citryCallc8b874e9279def47.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Delete")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["df0f51fd20e8d0e495515275607cceed7e56cc2c1ea9785e2de51e6ef3f222dd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall28946b3e32edd524","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld28748ba57c350d8","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc8b874e9279def47","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallebf22779e640ecac","typeKey":"CAlertDialog_4d9fc7","componentTag":"citry-c-alert-dialog-64bb695e","bindings":[],"fills":[{"name":"citrySlot21cd47f4d34f88de","localDescendants":["citryCall28946b3e32edd524"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot7b13e33c0cc31ff6","localDescendants":["citryCalld28748ba57c350d8"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9863a0b3c4618db6","localDescendants":["citryCallc8b874e9279def47"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlota955e5fc6e74cd26","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote1d483eaca719f83","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_alert_dialog_glance_d47db903 = _resolveComponent("citry-alert-dialog-glance-d47db903")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_alert_dialog_glance_d47db903, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall95c7e1a36eee8740.id,
      key: _ctx.$citryPrepared.calls.citryCall95c7e1a36eee8740.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["86091cdfbdaaccee79568ced6cd7d9a8c508a9a3d113d953b3b59307b8893858"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall95c7e1a36eee8740","typeKey":"AlertDialogGlance_b0012e","componentTag":"citry-alert-dialog-glance-d47db903","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
