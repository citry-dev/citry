(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-command-palette-host",
    "data-citry-command-palette-host": ""
  }, [
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
          _createElementVNode("section", _mergeProps({
            role: "group",
            "data-citry-ui-part": "command-palette-group"
          }, _ctx.$citryPrepared.citryAttrs6), [
            _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "command-palette-group-label" }, _ctx.$citryPrepared.citryAttrs7), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */),
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
          _createElementVNode("hr", _mergeProps({
            "aria-hidden": "true",
            "data-citry-ui-part": "command-palette-separator"
          }, _ctx.$citryPrepared.citryAttrs12), null, 16 /* FULL_PROPS */),
          _createElementVNode("section", _mergeProps({
            role: "group",
            "data-citry-ui-part": "command-palette-group"
          }, _ctx.$citryPrepared.citryAttrs13), [
            _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "command-palette-group-label" }, _ctx.$citryPrepared.citryAttrs14), _toDisplayString(_ctx.$citryPrepared.citryText5), 17 /* TEXT, FULL_PROPS */),
            _createElementVNode("div", _mergeProps({
              role: "option",
              "aria-selected": "false",
              "data-citry-ui-part": "command-palette-command"
            }, _ctx.$citryPrepared.citryAttrs15), [
              _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs16)), _toDisplayString(_ctx.$citryPrepared.citryText6), 17 /* TEXT, FULL_PROPS */),
              _createElementVNode("span", {
                class: "cui-command-palette__shortcut",
                inert: "",
                "aria-hidden": "true",
                "data-citry-ui-part": "command-palette-item-end"
              }, _toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("div", _mergeProps({
              role: "option",
              "aria-selected": "false",
              "data-citry-ui-part": "command-palette-command"
            }, _ctx.$citryPrepared.citryAttrs17), [
              _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs18)), _toDisplayString(_ctx.$citryPrepared.citryText8), 17 /* TEXT, FULL_PROPS */),
              _createElementVNode("span", _mergeProps({ class: "cui-command-palette__description" }, _ctx.$citryPrepared.citryAttrs19), _toDisplayString(_ctx.$citryPrepared.citryText9), 17 /* TEXT, FULL_PROPS */)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot5d40b05a1c222f74", { key: 0 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 1 }, _toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9fb157228e0a81ed9e8b3e5374a19b8003dbe37d4c3a0197f020096305182803"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-records" }, [
    _createElementVNode("h2", null, "Frozen Python records"),
    _createElementVNode("p", null, "The rendered palette preserves group, separator, and command order."),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla2ec1cd61867b052.id,
      key: _ctx.$citryPrepared.calls.citryCalla2ec1cd61867b052.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c84c21bd05ee6fbdc3ce8a96a74e5888a58d28319d2e7a2e050b1996b25f5b5f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla2ec1cd61867b052","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_python_command_records_b5fadd33 = _resolveComponent("citry-python-command-records-b5fadd33")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_python_command_records_b5fadd33, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall86d3715cf4a1ed6f.id,
      key: _ctx.$citryPrepared.calls.citryCall86d3715cf4a1ed6f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e5a4598df7078c61ea8fa685e36de60a9a7aae4c7345bc1f052f2188a56881c9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall86d3715cf4a1ed6f","typeKey":"PythonCommandRecords_6b9f3e","componentTag":"citry-python-command-records-b5fadd33","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
