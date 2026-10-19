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
        ]),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot200675c295c67c7c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot200675c295c67c7c", { key: 3 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["eef909811aab5baafdaf311f173ae474434a371c3484d403a953d18d1dbbc536"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "controlled-dialog" }, [
    _createElementVNode("p", null, "Mission control"),
    _createElementVNode("h2", null, "Own every visibility change"),
    _createElementVNode("label", { class: "controlled-dialog__toggle" }, [
      _withDirectives(_createElementVNode("input", {
        key: "citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a",
        type: "checkbox",
        "onUpdate:modelValue": $event => ((_ctx.accept) = $event)
      }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelCheckbox, _ctx.accept],
        [_directive_citry_vue_owned, 'checked']
      ]),
      _createTextVNode(" Accept Dialog requests ")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
      open: _ctx.open,
      onOpenChange: (nextOpen, detail) => {
        _ctx.lastReason = detail.reason;
        if (_ctx.accept) _ctx.open = nextOpen;
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCallc17765b0fbaeb849.id,
      key: _ctx.$citryPrepared.calls.citryCallc17765b0fbaeb849.key
    }, {
      ['citrySlot39e9540beec747a3']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallff785060bb4333d8.id,
          key: _ctx.$citryPrepared.calls.citryCallff785060bb4333d8.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Request flight plan ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
        _createTextVNode(" Flight plan ")
      ]),
      ['citrySlot4c119cf029159074']: _withCtx(() => [
        _createTextVNode(" Controlled owners may accept or decline this close request. ")
      ]),
      ['citrySlot200675c295c67c7c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall75f93066fb44d9f2.id,
          key: _ctx.$citryPrepared.calls.citryCall75f93066fb44d9f2.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" Request close ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "citry-id"])),
    _createElementVNode("p", {
      class: "controlled-dialog__status",
      "aria-live": "polite"
    }, [
      _createTextVNode(" Last request: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.lastReason)
      }, "none", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fadac3dd5218f41dab6301373f4d23c60d87ef1ed3b81794c2e71091dcf93802"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2","replacementKey":"citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCallff785060bb4333d8","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall75f93066fb44d9f2","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc17765b0fbaeb849","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":285,"sourceEnd":297},{"kind":"prop","name":":onOpenChange","value":"(nextOpen, detail) => {\n        lastReason = detail.reason;\n        if (accept) open = nextOpen;\n      }","sourceStart":298,"sourceEnd":418}],"fills":[{"name":"citrySlot200675c295c67c7c","localDescendants":["citryCall75f93066fb44d9f2"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCallff785060bb4333d8"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_dialog_84cd81e7 = _resolveComponent("citry-controlled-dialog-84cd81e7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_dialog_84cd81e7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb4658754c5ddff73.id,
      key: _ctx.$citryPrepared.calls.citryCallb4658754c5ddff73.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["609254fc777d084339c7abb85222f698fdd06c4defbb1ed14f02bf79d1e2be73"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb4658754c5ddff73","typeKey":"ControlledDialog_658a27","componentTag":"citry-controlled-dialog-84cd81e7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
