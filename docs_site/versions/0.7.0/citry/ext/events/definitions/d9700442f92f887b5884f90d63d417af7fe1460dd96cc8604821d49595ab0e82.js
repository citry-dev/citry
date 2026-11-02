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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  
  return (_openBlock(), _createElementBlock("section", { class: "field-note" }, [
    _createElementVNode("p", null, "Tonight's observation"),
    _createElementVNode("h2", null, "Aurora over the northern ridge"),
    (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle604c849eb8f2708.id,
      key: _ctx.$citryPrepared.calls.citryCalle604c849eb8f2708.key
    }, {
      ['citrySlot01f533d219338d4d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall5addf573514aca0d.id,
          key: _ctx.$citryPrepared.calls.citryCall5addf573514aca0d.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Read field note ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot81c7ca490fc15941']: _withCtx(() => [
        _createTextVNode(" Aurora over the northern ridge ")
      ]),
      ['citrySlotf0252007f9ecd074']: _withCtx(() => [
        _createTextVNode(" Recorded at 01:42 under a clear sky. ")
      ]),
      ['citrySlotc18de8dd8e2a7fea']: _withCtx(() => [
        _createElementVNode("p", null, " Green ribbons appeared low on the horizon, then climbed toward the zenith in three bright arcs. ")
      ]),
      ['citrySlot02ca7b57762cc54c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallcfbd66fad827c299.id,
          key: _ctx.$citryPrepared.calls.citryCallcfbd66fad827c299.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Close note ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallead242c5b2b3e56a.id,
          key: _ctx.$citryPrepared.calls.citryCallead242c5b2b3e56a.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Add to atlas ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ca4c7de4b90d6d51067aa635a7e5f5d004560c2f3236f49841d37054698bb8da"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5addf573514aca0d","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcfbd66fad827c299","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallead242c5b2b3e56a","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle604c849eb8f2708","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot01f533d219338d4d","localDescendants":["citryCall5addf573514aca0d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot02ca7b57762cc54c","localDescendants":["citryCallcfbd66fad827c299","citryCallead242c5b2b3e56a"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot81c7ca490fc15941","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc18de8dd8e2a7fea","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf0252007f9ecd074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_open_field_note_2ab19b73 = _resolveComponent("citry-open-field-note-2ab19b73")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_open_field_note_2ab19b73, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1be820e4412ca6dd.id,
      key: _ctx.$citryPrepared.calls.citryCall1be820e4412ca6dd.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a07c76d7d25d5d62fc935a93fa755f3a550b3bf57cb09febe429810fdbddda59"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1be820e4412ca6dd","typeKey":"OpenFieldNote_542496","componentTag":"citry-open-field-note-2ab19b73","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
