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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-disclosure",
    "data-citry-disclosure-root": "",
    "data-citry-ui-part": "disclosure"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-disclosure__header",
      "data-citry-ui-part": "disclosure-header"
    }, [
      _createElementVNode("citry-dynamic-f4170320eb7443cf", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
        _createElementVNode("button", _mergeProps({
          class: "cui-disclosure__trigger",
          type: "button",
          "data-citry-disclosure-trigger": "",
          "data-citry-ui-part": "disclosure-trigger"
        }, _ctx.$citryPrepared.citryAttrs2), [
          _createElementVNode("span", {
            class: "cui-disclosure__title",
            "data-citry-ui-part": "disclosure-title"
          }, [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e2ca619259b58f7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e2ca619259b58f7", { key: 0 })
              : _createCommentVNode("v-if", true)
          ]),
          (_openBlock(), _createElementBlock("span", {
            class: "cui-disclosure__indicator",
            "aria-hidden": "true",
            "data-citry-ui-part": "disclosure-indicator"
          }, [
            (_openBlock(), _createElementBlock("svg", {
              xmlns: "http://www.w3.org/2000/svg",
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              focusable: "false",
              "aria-hidden": "true"
            }, [
              _createElementVNode("path", { d: "m6 9 6 6 6-6" })
            ]))
          ]))
        ], 16 /* FULL_PROPS */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-disclosure__actions",
        "data-citry-ui-part": "disclosure-actions"
      }, _ctx.$citryPrepared.citryAttrs3), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot27128b767c06ba6f'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot27128b767c06ba6f", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-disclosure__panel",
      "data-citry-disclosure-panel": "",
      "data-citry-ui-part": "disclosure-panel"
    }, _ctx.$citryPrepared.citryAttrs4), [
      _createElementVNode("div", {
        class: "cui-disclosure__body",
        "data-citry-ui-part": "disclosure-body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotea4781f0f1286df5'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotea4781f0f1286df5", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["21a11446d46ec43167da97255f62b9f9808792c5dcc166f6ae3d4b65de3a81fb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-disclosure",
    "data-citry-disclosure-root": "",
    "data-citry-ui-part": "disclosure"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-disclosure__header",
      "data-citry-ui-part": "disclosure-header"
    }, [
      _createElementVNode("citry-dynamic-f4170320eb7443cf", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
        _createElementVNode("button", _mergeProps({
          class: "cui-disclosure__trigger",
          type: "button",
          "data-citry-disclosure-trigger": "",
          "data-citry-ui-part": "disclosure-trigger"
        }, _ctx.$citryPrepared.citryAttrs2), [
          _createElementVNode("span", {
            class: "cui-disclosure__title",
            "data-citry-ui-part": "disclosure-title"
          }, [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e2ca619259b58f7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e2ca619259b58f7", { key: 0 })
              : _createCommentVNode("v-if", true)
          ]),
          (_openBlock(), _createElementBlock("span", {
            class: "cui-disclosure__indicator",
            "aria-hidden": "true",
            "data-citry-ui-part": "disclosure-indicator"
          }, [
            (_openBlock(), _createElementBlock("svg", {
              xmlns: "http://www.w3.org/2000/svg",
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              "stroke-linecap": "round",
              "stroke-linejoin": "round",
              focusable: "false",
              "aria-hidden": "true"
            }, [
              _createElementVNode("path", { d: "m6 9 6 6 6-6" })
            ]))
          ]))
        ], 16 /* FULL_PROPS */)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-disclosure__panel",
      "data-citry-disclosure-panel": "",
      "data-citry-ui-part": "disclosure-panel"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("div", {
        class: "cui-disclosure__body",
        "data-citry-ui-part": "disclosure-body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot24b36c89b7f055eb'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot24b36c89b7f055eb", { key: 1 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1b5a53bf67453b241b2aab6a3f11b14676d1d563e7228ee4a9183e6e7c6bad0f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_disclosure_63b10531 = _resolveComponent("citry-c-disclosure-63b10531")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "disclosure-actions-demo" }, [
    (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb45f24bf078e776d.id,
      key: _ctx.$citryPrepared.calls.citryCallb45f24bf078e776d.key
    }, {
      ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
        _createTextVNode("Release notes")
      ]),
      ['citrySlot27128b767c06ba6f']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1a465c665572e334.id,
          key: _ctx.$citryPrepared.calls.citryCall1a465c665572e334.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Copy link")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlotea4781f0f1286df5']: _withCtx(() => [
        _createTextVNode("Review migration notes before deploying version 4.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
      disabled: _ctx.disabled,
      "citry-id": _ctx.$citryPrepared.calls.citryCall44eeec7f3e7c7ede.id,
      key: _ctx.$citryPrepared.calls.citryCall44eeec7f3e7c7ede.key
    }, {
      ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
        _createTextVNode("Managed policy")
      ]),
      ['citrySlot24b36c89b7f055eb']: _withCtx(() => [
        _createTextVNode("Your organization keeps this guidance visible.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["disabled", "citry-id"])),
    _createElementVNode("label", null, [
      _withDirectives(_createElementVNode("input", {
        key: "citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a",
        type: "checkbox",
        "onUpdate:modelValue": $event => ((_ctx.disabled) = $event)
      }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelCheckbox, _ctx.disabled],
        [_directive_citry_vue_owned, 'checked']
      ]),
      _createTextVNode(" Disable managed policy")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2470fd7ca7973a2e.id,
      key: _ctx.$citryPrepared.calls.citryCall2470fd7ca7973a2e.key
    }, {
      ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
        _createTextVNode("Unavailable audit appendix")
      ]),
      ['citrySlot24b36c89b7f055eb']: _withCtx(() => [
        _createTextVNode("This closed section cannot be activated.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("fieldset", { disabled: _ctx.fieldsetDisabled }, [
      _createElementVNode("legend", null, [
        _createElementVNode("label", null, [
          _withDirectives(_createElementVNode("input", {
            key: "citryReplacementb0f01f6427d1c43c5d491544fbeacebcbd0de91a3d9beded616ef0b57039ead0",
            type: "checkbox",
            "onUpdate:modelValue": $event => ((_ctx.fieldsetDisabled) = $event)
          }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
            [_vModelCheckbox, _ctx.fieldsetDisabled],
            [_directive_citry_vue_owned, 'checked']
          ]),
          _createTextVNode(" Disable native fieldset")
        ])
      ]),
      (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallc3671dec68a3753e.id,
        key: _ctx.$citryPrepared.calls.citryCallc3671dec68a3753e.key
      }, {
        ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
          _createTextVNode("Fieldset-owned policy")
        ]),
        ['citrySlot24b36c89b7f055eb']: _withCtx(() => [
          _createTextVNode("Native fieldset ownership disables this trigger.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ], 8 /* PROPS */, ["disabled"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c0c6f44e7c8718ba5262a7d075255cdf2fc4ad88f762f0ef55715665d7b7950a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective1b5b4f91c11c31cd1c5b49e19b813d6f4c778465e8679128af467dc8e8c25e0cD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective1b5b4f91c11c31cd1c5b49e19b813d6f4c778465e8679128af467dc8e8c25e0c","replacementKey":"citryReplacementb0f01f6427d1c43c5d491544fbeacebcbd0de91a3d9beded616ef0b57039ead0","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2","replacementKey":"citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall1a465c665572e334","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb45f24bf078e776d","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot27128b767c06ba6f","localDescendants":["citryCall1a465c665572e334"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotea4781f0f1286df5","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall44eeec7f3e7c7ede","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[{"kind":"prop","name":":disabled","value":"disabled","sourceStart":743,"sourceEnd":763}],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot24b36c89b7f055eb","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2470fd7ca7973a2e","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot24b36c89b7f055eb","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc3671dec68a3753e","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot24b36c89b7f055eb","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_disclosure_actions_and_disabled_36d7059c = _resolveComponent("citry-disclosure-actions-and-disabled-36d7059c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_disclosure_actions_and_disabled_36d7059c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6fa59a5d71aff39b.id,
      key: _ctx.$citryPrepared.calls.citryCall6fa59a5d71aff39b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["523158819587e1492db34f6ab0658534dffbd059f63d94dfcfc22ba9a1a82f97"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6fa59a5d71aff39b","typeKey":"DisclosureActionsAndDisabled_92430d","componentTag":"citry-disclosure-actions-and-disabled-36d7059c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
