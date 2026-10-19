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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e877023af7586584d9b0445405f248eed3c20ad2f1b822c9755e2273f344c49d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f4170320eb7443cf","tag":"h3","sourceStart":207,"sourceEnd":275}]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_disclosure_63b10531 = _resolveComponent("citry-c-disclosure-63b10531")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "controlled-disclosure" }, [
    (_openBlock(), _createBlock(_component_citry_c_disclosure_63b10531, {
      open: _ctx.controlled ? _ctx.open : null,
      onOpenChange: (next, detail) => {
        _ctx.last = `${detail.source}: ${next ? 'open' : 'closed'}`;
        if (_ctx.controlled && _ctx.accept) _ctx.open = next;
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCallb5bf07abca841f48.id,
      key: _ctx.$citryPrepared.calls.citryCallb5bf07abca841f48.key
    }, {
      ['citrySlot0e2ca619259b58f7']: _withCtx(() => [
        _createTextVNode("Advanced logging")
      ]),
      ['citrySlot24b36c89b7f055eb']: _withCtx(() => [
        _createTextVNode(" Include request identifiers and timing details in diagnostic output. ")
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
      _createTextVNode(" Accept trigger requests ")
    ]),
    _createElementVNode("div", {
      class: "controlled-disclosure__controls",
      role: "group",
      "aria-label": "Disclosure owner controls"
    }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.controlled=true; _ctx.open=true}
      }, "Show", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.controlled=true; _ctx.open=false}
      }, "Hide", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.controlled=false)
      }, "Release control", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("output", null, [
      _createTextVNode(" Ownership: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.controlled ? 'browser-controlled' : 'released')
      }, "browser-controlled", 8 /* PROPS */, ["textContent"]),
      _createTextVNode(" · Requests: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.accept ? 'accepted' : 'refused')
      }, "accepted", 8 /* PROPS */, ["textContent"]),
      _createTextVNode(" · Last: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.last)
      }, "none", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a45f3eece9279d584ab0b3337fb3c04cef6f50ad7a60a75fb5b4eddc5a20fa74"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectiveffdd13fb8993635c7ecd9dd4eac9dcd3fa03a9d08fe8a445a5adf01d054415c3D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectiveffdd13fb8993635c7ecd9dd4eac9dcd3fa03a9d08fe8a445a5adf01d054415c3","replacementKey":"citryReplacement7c02699b4780407cd81cbbbb7a4dbda9a849154ec28b4d56d0e25a5d59912220","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCallb5bf07abca841f48","typeKey":"CDisclosure_c778df","componentTag":"citry-c-disclosure-63b10531","bindings":[{"kind":"prop","name":":open","value":"controlled ? open : null","sourceStart":72,"sourceEnd":104},{"kind":"prop","name":":onOpenChange","value":"(next, detail) => {\n        last = `${detail.source}: ${next ? 'open' : 'closed'}`;\n        if (controlled && accept) open = next;\n      }","sourceStart":105,"sourceEnd":259}],"fills":[{"name":"citrySlot0e2ca619259b58f7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot24b36c89b7f055eb","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_disclosure_047eb36b = _resolveComponent("citry-controlled-disclosure-047eb36b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_disclosure_047eb36b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0be7a7d9ad91f43c.id,
      key: _ctx.$citryPrepared.calls.citryCall0be7a7d9ad91f43c.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6eafe163a2445a2fb88f0df9683a1bb12d0a5b44414434015059c3dc20795c20"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0be7a7d9ad91f43c","typeKey":"ControlledDisclosure_d39257","componentTag":"citry-controlled-disclosure-047eb36b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
