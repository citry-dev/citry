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
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot4c119cf029159074'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot4c119cf029159074", { key: 2 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8c0878bf9747556de54b1f24281346a3e9c755093ba4ac00b0b293e786f7f1d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "dialog-focus-grid" }, [
    _createElementVNode("article", null, [
      _createElementVNode("p", null, "Quick observation"),
      _createElementVNode("h2", null, "Focus a control"),
      (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall93f90cea8c43c84c.id,
        key: _ctx.$citryPrepared.calls.citryCall93f90cea8c43c84c.key
      }, {
        ['citrySlot39e9540beec747a3']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            onClick: $event => (_ctx.$refs.cometName.setAttribute('autofocus', '')),
            "citry-id": _ctx.$citryPrepared.calls.citryCalld90a05ee8f771490.id,
            key: _ctx.$citryPrepared.calls.citryCalld90a05ee8f771490.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Name a comet ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"]))
        ]),
        ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
          _createTextVNode(" Name a comet ")
        ]),
        ['citrySlot4c119cf029159074']: _withCtx(() => [
          _createElementVNode("label", { for: "comet-name" }, "Catalog name"),
          _withDirectives(_createElementVNode("input", {
            id: "comet-name",
            ref: "cometName"
          }, null, 512 /* NEED_PATCH */), [
            [_directive_citry_vue_owned, []]
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("p", null, "Long report"),
      _createElementVNode("h2", null, "Focus the title"),
      (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall9eb6e4014a788bca.id,
        key: _ctx.$citryPrepared.calls.citryCall9eb6e4014a788bca.key
      }, {
        ['citrySlot39e9540beec747a3']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall3cbf146ea5848ac9.id,
            key: _ctx.$citryPrepared.calls.citryCall3cbf146ea5848ac9.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Read eclipse report ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
          _createTextVNode(" Total eclipse report ")
        ]),
        ['citrySlot4c119cf029159074']: _withCtx(() => [
          _createElementVNode("p", null, " Focusing the title starts reading at the top without jumping past structured content. "),
          _createElementVNode("button", { type: "button" }, "Continue reading")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e52fa7a6758c6ae0ed927387c26f38536ebd1a35492ea0677079fd15b66131a1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld90a05ee8f771490","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"$refs.cometName.setAttribute('autofocus', '')","sourceStart":337,"sourceEnd":391}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall93f90cea8c43c84c","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCalld90a05ee8f771490"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3cbf146ea5848ac9","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9eb6e4014a788bca","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCall3cbf146ea5848ac9"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_dialog_initial_focus_949cd3f0 = _resolveComponent("citry-dialog-initial-focus-949cd3f0")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_dialog_initial_focus_949cd3f0, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall68fc4d0db762891e.id,
      key: _ctx.$citryPrepared.calls.citryCall68fc4d0db762891e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c643781d9b8fa1598e9288801b9cab8d9c81163d5338bb024cb8108c3eba6b48"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall68fc4d0db762891e","typeKey":"DialogInitialFocus_1b7b2a","componentTag":"citry-dialog-initial-focus-949cd3f0","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
