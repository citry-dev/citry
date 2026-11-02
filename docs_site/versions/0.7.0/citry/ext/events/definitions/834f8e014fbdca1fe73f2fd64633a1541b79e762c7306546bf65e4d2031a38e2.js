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
              _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs16)), _toDisplayString(_ctx.$citryPrepared.citryText6), 17 /* TEXT, FULL_PROPS */)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("div", _mergeProps({
              role: "option",
              "aria-selected": "false",
              "data-citry-ui-part": "command-palette-command"
            }, _ctx.$citryPrepared.citryAttrs17), [
              _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs18)), _toDisplayString(_ctx.$citryPrepared.citryText7), 17 /* TEXT, FULL_PROPS */),
              _createElementVNode("span", _mergeProps({ class: "cui-command-palette__description" }, _ctx.$citryPrepared.citryAttrs19), _toDisplayString(_ctx.$citryPrepared.citryText8), 17 /* TEXT, FULL_PROPS */)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot2b1da198118e4ee7", { key: 0 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 1 }, _toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9883a4184a6d821860f861f867ba3f50b0acbddf05787977243970add81a7164"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c919b946abcd97432bb96114edd8b7d944ee97ded3ab74c2eb53ff51eef743d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla2ec1cd61867b052","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_python_command_records_9cd48744 = _resolveComponent("citry-python-command-records-9cd48744")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_python_command_records_9cd48744, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla2efc6dfb6c4fa02.id,
      key: _ctx.$citryPrepared.calls.citryCalla2efc6dfb6c4fa02.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3511b1908344929c1a2dae24f6d4eaa8c7cbc45d7cf6ec86ae5d0fc884ace8e4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla2efc6dfb6c4fa02","typeKey":"PythonCommandRecords_905f44","componentTag":"citry-python-command-records-9cd48744","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
