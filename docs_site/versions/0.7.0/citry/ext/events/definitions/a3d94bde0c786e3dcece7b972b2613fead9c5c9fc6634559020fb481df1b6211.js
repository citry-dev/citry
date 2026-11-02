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
    class: "cui-drawer-host",
    "data-citry-drawer-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot523f58f7814a4d8f'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot523f58f7814a4d8f", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-drawer",
      "aria-modal": "true",
      "data-citry-ui-part": "drawer"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", {
        class: "cui-drawer__surface",
        "data-citry-ui-part": "surface"
      }, [
        _createElementVNode("header", {
          class: "cui-drawer__header",
          "data-citry-ui-part": "header"
        }, [
          _createElementVNode("h2", _mergeProps({
            class: "cui-drawer__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs1), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot407b993ac6d0fc2e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot407b993ac6d0fc2e", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            class: "cui-drawer__close",
            type: "button",
            "data-citry-drawer-close": "",
            "data-citry-drawer-built-in-close": "",
            "data-citry-ui-part": "close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, "×")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-drawer__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot22759ec5a12d3f94'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot22759ec5a12d3f94", { key: 2 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["59d710aaddb48b7afe5e1faa0e02287494733882144b70bb03933e5d9c888cfe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_drawer_7a79445f = _resolveComponent("citry-c-drawer-7a79445f")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "controlled-drawer" }, [
    (_openBlock(), _createBlock(_component_citry_c_drawer_7a79445f, {
      open: _ctx.open,
      onOpenChange: _ctx.applyOpenRequest,
      "citry-id": _ctx.$citryPrepared.calls.citryCall2d702cf9eddfc06b.id,
      key: _ctx.$citryPrepared.calls.citryCall2d702cf9eddfc06b.key
    }, {
      ['citrySlot523f58f7814a4d8f']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall5516cfeba1e5ade4.id,
          key: _ctx.$citryPrepared.calls.citryCall5516cfeba1e5ade4.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Controlled archive")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot407b993ac6d0fc2e']: _withCtx(() => [
        _createTextVNode("Controlled archive")
      ]),
      ['citrySlot22759ec5a12d3f94']: _withCtx(() => [
        _createTextVNode("The owner may accept or decline visibility requests.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "citry-id"])),
    _createElementVNode("label", null, [
      _withDirectives(_createElementVNode("input", {
        key: "citryReplacement7c02699b4780407cd81cbbbb7a4dbda9a849154ec28b4d56d0e25a5d59912220",
        type: "checkbox",
        "onUpdate:modelValue": $event => ((_ctx.accept) = $event)
      }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelCheckbox, _ctx.accept],
        [_directive_citry_vue_owned, 'checked']
      ]),
      _createTextVNode(" Accept requests")
    ]),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.log)
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ef07f6eb79e7a999330e9d8f1146918c57a4f096a917c8a1be76172ecc8104b3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectiveffdd13fb8993635c7ecd9dd4eac9dcd3fa03a9d08fe8a445a5adf01d054415c3D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectiveffdd13fb8993635c7ecd9dd4eac9dcd3fa03a9d08fe8a445a5adf01d054415c3","replacementKey":"citryReplacement7c02699b4780407cd81cbbbb7a4dbda9a849154ec28b4d56d0e25a5d59912220","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall5516cfeba1e5ade4","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2d702cf9eddfc06b","typeKey":"CDrawer_01cc33","componentTag":"citry-c-drawer-7a79445f","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":64,"sourceEnd":76},{"kind":"prop","name":":onOpenChange","value":"applyOpenRequest","sourceStart":77,"sourceEnd":109}],"fills":[{"name":"citrySlot22759ec5a12d3f94","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot407b993ac6d0fc2e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot523f58f7814a4d8f","localDescendants":["citryCall5516cfeba1e5ade4"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_drawer_682009d3 = _resolveComponent("citry-controlled-drawer-682009d3")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_drawer_682009d3, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall629c7a344be97a05.id,
      key: _ctx.$citryPrepared.calls.citryCall629c7a344be97a05.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a7d637348a1eabe6a8ba467a32b519660382e0c3aeaabbfd65535084a5339048"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall629c7a344be97a05","typeKey":"ControlledDrawer_18d9c2","componentTag":"citry-controlled-drawer-682009d3","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
