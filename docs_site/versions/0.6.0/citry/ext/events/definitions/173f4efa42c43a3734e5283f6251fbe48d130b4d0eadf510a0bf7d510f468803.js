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
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-command-palette-host",
    "data-citry-command-palette-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot888a02f3e7487045'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot888a02f3e7487045", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-command-palette",
      "data-citry-command-palette-root": "",
      "data-citry-ui-part": "command-palette"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("section", {
        class: "cui-command-palette__surface",
        "data-citry-ui-part": "command-palette-surface"
      }, [
        _createElementVNode("header", {
          class: "cui-command-palette__header",
          "data-citry-ui-part": "command-palette-header"
        }, [
          _createElementVNode("h2", _mergeProps({ "data-citry-ui-part": "command-palette-title" }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            "data-citry-command-palette-close": "",
            "data-citry-ui-part": "command-palette-close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, "×")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("search", { "data-citry-ui-part": "command-palette-search" }, [
          _createElementVNode("label", _mergeProps({
            class: "cui-command-palette__visually-hidden",
            "data-citry-ui-part": "command-palette-search-label"
          }, _ctx.$citryPrepared.citryAttrs3), [
            _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
          ], 16 /* FULL_PROPS */),
          _withDirectives(_createElementVNode("input", _mergeProps({
            type: "text",
            role: "combobox",
            autocomplete: "off",
            autofocus: "",
            disabled: "",
            "aria-autocomplete": "list",
            "data-citry-ui-part": "command-palette-input"
          }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
            [_directive_citry_vue_owned, ['checked','value']]
          ])
        ]),
        _createElementVNode("div", _mergeProps({
          role: "listbox",
          "data-citry-ui-part": "command-palette-listbox"
        }, _ctx.$citryPrepared.citryAttrs5), [
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs6), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs7)), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs8), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs9)), _toDisplayString(_ctx.$citryPrepared.citryText3), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs10), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs11)), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot5d40b05a1c222f74", { key: 1 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 2 }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["540fd6cfbf49bba91f2f995bb26581dff6a6151f5e4a6a280000a27942f8ed17"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  
  return (_openBlock(), _createElementBlock("form", {
    ref: "form",
    id: "command-palette-profile-form",
    class: "command-palette-form",
    onSubmit: _withModifiers($event => (_ctx.submits++), ["prevent"])
  }, [
    _createElementVNode("h2", null, "Profile Form"),
    _createElementVNode("label", null, [
      _createTextVNode("Display name "),
      _createElementVNode("input", {
        ref: "nameInput",
        id: "command-profile-name",
        name: "display_name",
        value: "Ada"
      }, null, 512 /* NEED_PATCH */)
    ]),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.open,
      query: _ctx.query,
      onOpenChange: (value)=>_ctx.open=value,
      onQueryChange: (value)=>_ctx.query=value,
      onAction: _ctx.runAction,
      "citry-id": _ctx.$citryPrepared.calls.citryCallc824724969d4b9b1.id,
      key: _ctx.$citryPrepared.calls.citryCallc824724969d4b9b1.key
    }, {
      ['citrySlot888a02f3e7487045']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall7a2d7a0940f46c3e.id,
          key: _ctx.$citryPrepared.calls.citryCall7a2d7a0940f46c3e.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Open profile commands")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "query", "onOpenChange", "onQueryChange", "onAction", "citry-id"])),
    _createElementVNode("button", { type: "submit" }, "Save profile"),
    _createElementVNode("output", { "aria-live": "polite" }, [
      _createTextVNode(" Native submits: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.submits)
      }, "0", 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; palette actions: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.actions)
      }, "0", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("p", null, " IME fixture: composition Enter and Escape remain native; ordinary palette Enter never submits this Form unless the action callback asks. ")
  ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["260e6b04c9c01676c6d87836bc7ea22c47a667ce2581246bdc2685fddf0e444f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7a2d7a0940f46c3e","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc824724969d4b9b1","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":283,"sourceEnd":295},{"kind":"prop","name":":query","value":"query","sourceStart":296,"sourceEnd":310},{"kind":"prop","name":":onOpenChange","value":"(value)=>open=value","sourceStart":311,"sourceEnd":346},{"kind":"prop","name":":onQueryChange","value":"(value)=>query=value","sourceStart":347,"sourceEnd":384},{"kind":"prop","name":":onAction","value":"runAction","sourceStart":385,"sourceEnd":406}],"fills":[{"name":"citrySlot888a02f3e7487045","localDescendants":["citryCall7a2d7a0940f46c3e"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_form_safe_palette_cbf0053c = _resolveComponent("citry-form-safe-palette-cbf0053c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_form_safe_palette_cbf0053c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla6fd4e791204ff63.id,
      key: _ctx.$citryPrepared.calls.citryCalla6fd4e791204ff63.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["81ce17d814499f695e281d1fabf0e1425e7d696dfec24173b12c1943e11d8f2b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla6fd4e791204ff63","typeKey":"FormSafePalette_1111a5","componentTag":"citry-form-safe-palette-cbf0053c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
