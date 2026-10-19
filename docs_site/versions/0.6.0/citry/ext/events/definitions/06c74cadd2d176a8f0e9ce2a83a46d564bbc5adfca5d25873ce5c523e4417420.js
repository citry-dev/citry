(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["20c4ae04f4a1879a02d0442bd41cabdb0c8a0f9ac8e8fe2cc4c5f38618238e8f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", _mergeProps({
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), " * ", 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["16855a0653b93f5f61718859e64fd873868d1b391d34238f9b2730faa47cc86c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
  return (_openBlock(), _createElementBlock("form", _mergeProps({
    ref: "root",
    class: "cui-form",
    "data-citry-ui-part": "form"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("fieldset", {
      class: "cui-form__fieldset",
      "data-citry-ui-part": "fieldset"
    }, [
      _createElementVNode("legend", {
        hidden: "",
        "aria-hidden": "true"
      }),
      (_ctx.$citryPrepared.selectedSlots['citrySlotf39a0a3e8a179bdf'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotf39a0a3e8a179bdf", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["81a1fc957f2a8755f8ce082405e4e351c8f4f04f20700087e02025fa7a4b1a92"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_input_743f5a7c = _resolveComponent("citry-c-input-743f5a7c")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_form_54ae8704 = _resolveComponent("citry-c-form-54ae8704")
  
  return (_openBlock(), _createElementBlock("section", { class: "plate-solve" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Astrometry pipeline"),
      _createElementVNode("h2", null, "Solve a star field")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_form_54ae8704, {
      submitting: _ctx.submitting,
      onSubmit: _withModifiers($event => {
      _ctx.attempts += 1;
      _ctx.snapshot = JSON.stringify(Object.fromEntries(new window.FormData($event.target)));
      _ctx.submitting = true;
    }, ["prevent"]),
      "citry-id": _ctx.$citryPrepared.calls.citryCall89c80cd4b00a70df.id,
      key: _ctx.$citryPrepared.calls.citryCall89c80cd4b00a70df.key
    }, {
      ['citrySlotf39a0a3e8a179bdf']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld9b3cc83fd5a1f44.id,
          key: _ctx.$citryPrepared.calls.citryCalld9b3cc83fd5a1f44.key
        }, {
          ['citrySlote2526e6f745e4169']: _withCtx(() => [
            _createTextVNode(" Frame ID ")
          ]),
          ['citrySlot6f90e269deb4619c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_input_743f5a7c, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall821b0b05b0f0fcda.id,
              key: _ctx.$citryPrepared.calls.citryCall821b0b05b0f0fcda.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        _createElementVNode("div", { class: "plate-solve__actions" }, [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            loading: _ctx.submitting,
            "citry-id": _ctx.$citryPrepared.calls.citryCalld8022bc04957fd92.id,
            key: _ctx.$citryPrepared.calls.citryCalld8022bc04957fd92.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Solve frame ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["loading", "citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            onClick: $event => (_ctx.submitting = false),
            "citry-id": _ctx.$citryPrepared.calls.citryCallc38f6ebfb4e17db0.id,
            key: _ctx.$citryPrepared.calls.citryCallc38f6ebfb4e17db0.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Finish request ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"]))
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["submitting", "onSubmit", "citry-id"])),
    _createElementVNode("p", {
      class: "plate-solve__status",
      "aria-live": "polite"
    }, [
      _createTextVNode(" Accepted submits: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.attempts)
      }, null, 8 /* PROPS */, ["textContent"]),
      _withDirectives(_createElementVNode("span", { key: "citryReplacementdd1931dd506a88ed51fb6eea478badb6b7b607d594a0c2f6b48eb3523d187cb3" }, [
        _createTextVNode(" · FormData "),
        _createElementVNode("code", {
          textContent: _toDisplayString(_ctx.snapshot)
        }, null, 8 /* PROPS */, ["textContent"])
      ], 512 /* NEED_PATCH */), [
        [_vShow, _ctx.snapshot]
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f8ad9a8af3a2e3134b71b7cb3098b4a6c4363ccac1f4393e35faeb1d6cddb23e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective5f13ec283e90a02bb6c7c6b9c5ae6e8d5204277945818b9b0c7fa7535337dfb8D0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective5f13ec283e90a02bb6c7c6b9c5ae6e8d5204277945818b9b0c7fa7535337dfb8","replacementKey":"citryReplacementdd1931dd506a88ed51fb6eea478badb6b7b607d594a0c2f6b48eb3523d187cb3","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall821b0b05b0f0fcda","typeKey":"CInput_dc895e","componentTag":"citry-c-input-743f5a7c","bindings":[]},{"localId":"citryCalld9b3cc83fd5a1f44","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall821b0b05b0f0fcda"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld8022bc04957fd92","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"prop","name":":loading","value":"submitting","sourceStart":1064,"sourceEnd":1085}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc38f6ebfb4e17db0","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"submitting = false","sourceStart":1349,"sourceEnd":1376}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall89c80cd4b00a70df","typeKey":"CForm_4a6900","componentTag":"citry-c-form-54ae8704","bindings":[{"kind":"prop","name":":submitting","value":"submitting","sourceStart":143,"sourceEnd":167},{"kind":"event","name":"@submit.prevent","value":"\n      attempts += 1;\n      snapshot = JSON.stringify(Object.fromEntries(new window.FormData($event.target)));\n      submitting = true;\n    ","sourceStart":168,"sourceEnd":326}],"fills":[{"name":"citrySlotf39a0a3e8a179bdf","localDescendants":["citryCall821b0b05b0f0fcda","citryCallc38f6ebfb4e17db0","citryCalld8022bc04957fd92","citryCalld9b3cc83fd5a1f44"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_submitting_guard_50131aac = _resolveComponent("citry-submitting-guard-50131aac")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_submitting_guard_50131aac, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6596c13b05203680.id,
      key: _ctx.$citryPrepared.calls.citryCall6596c13b05203680.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fafd79e7ad5bebda2b4ed6a7dd5780ec8aeb545e023b219d7f66fce8782463b7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6596c13b05203680","typeKey":"SubmittingGuard_64817e","componentTag":"citry-submitting-guard-50131aac","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
