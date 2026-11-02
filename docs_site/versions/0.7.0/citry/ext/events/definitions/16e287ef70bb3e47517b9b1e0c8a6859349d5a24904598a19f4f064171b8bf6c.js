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
              ? (_openBlock(), _createElementBlock("span", { key: 1 }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7e7ba5a24da3477d0ab0a4285897784e6005c8a9ba56437e06d7f061c7369d66"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, vModelCheckbox: _vModelCheckbox, vModelSelect: _vModelSelect, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-shortcut" }, [
    _createElementVNode("h2", null, "Application-owned Mod+K"),
    _createElementVNode("p", null, "Focus the app shell and press Mod+K. Editable targets stay native."),
    _createElementVNode("label", null, [
      _withDirectives(_createElementVNode("input", {
        key: "citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a",
        type: "checkbox",
        "onUpdate:modelValue": $event => ((_ctx.enabled) = $event)
      }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelCheckbox, _ctx.enabled],
        [_directive_citry_vue_owned, 'checked']
      ]),
      _createTextVNode(" Enable app shortcut")
    ]),
    _createElementVNode("label", null, [
      _createTextVNode(" Shortcut target "),
      _withDirectives(_createElementVNode("select", {
        key: "citryReplacement9f9eeffab06b9538192dffcca9cab7c9f6272fd77a2e85e24e39f0a3e271f131",
        "onUpdate:modelValue": $event => ((_ctx.target) = $event)
      }, [
        _createElementVNode("option", { value: "workspace" }, "Workspace palette"),
        _createElementVNode("option", { value: "help" }, "Help palette")
      ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelSelect, _ctx.target],
        [_directive_citry_vue_owned, 'selected']
      ])
    ]),
    _createElementVNode("label", null, [
      _createTextVNode("Unrelated input "),
      _createElementVNode("input", {
        type: "text",
        value: "Mod+K stays editable here"
      })
    ]),
    _createElementVNode("div", {
      contenteditable: "true",
      role: "textbox",
      "aria-label": "Editable application note"
    }, " Contenteditable shortcut exclusion "),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.workspaceOpen,
      onOpenChange: (value)=>_ctx.workspaceOpen=value,
      "citry-id": _ctx.$citryPrepared.calls.citryCalle46172e14d6776ed.id,
      key: _ctx.$citryPrepared.calls.citryCalle46172e14d6776ed.key
    }, null, 8 /* PROPS */, ["open", "onOpenChange", "citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.helpOpen,
      onOpenChange: (value)=>_ctx.helpOpen=value,
      "citry-id": _ctx.$citryPrepared.calls.citryCall79f552ebb41cd12b.id,
      key: _ctx.$citryPrepared.calls.citryCall79f552ebb41cd12b.key
    }, null, 8 /* PROPS */, ["open", "onOpenChange", "citry-id"])),
    _createElementVNode("output", null, [
      _createTextVNode("Handled app shortcuts: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.opens)
      }, "0", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3fa8571108a523ea7c738e3989c2bf235a6efdce80d5e72d411e77d6a882c726"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective6b3ddf72fb91269ee7e666926a70733c78da0bfd3574230a08e38878b351c94fD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective2062a29ba4362e3723343e9a237c19663ec3c859e483411f3104df4b51c4a1f2","replacementKey":"citryReplacementbda97311e8338d76ac5e02acaf98bb8c7a160b7c2fc1879f30978ad983d2d33a","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective6b3ddf72fb91269ee7e666926a70733c78da0bfd3574230a08e38878b351c94f","replacementKey":"citryReplacement9f9eeffab06b9538192dffcca9cab7c9f6272fd77a2e85e24e39f0a3e271f131","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCalle46172e14d6776ed","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"workspaceOpen","sourceStart":746,"sourceEnd":767},{"kind":"prop","name":":onOpenChange","value":"(value)=>workspaceOpen=value","sourceStart":768,"sourceEnd":812}]},{"localId":"citryCall79f552ebb41cd12b","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"helpOpen","sourceStart":1005,"sourceEnd":1021},{"kind":"prop","name":":onOpenChange","value":"(value)=>helpOpen=value","sourceStart":1022,"sourceEnd":1061}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_application_shortcut_b986f140 = _resolveComponent("citry-application-shortcut-b986f140")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_application_shortcut_b986f140, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall568601df10a7236f.id,
      key: _ctx.$citryPrepared.calls.citryCall568601df10a7236f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4314a2a698bdcda455f8830e8974b84791b4beb7f78236afae180e6410d72ec6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall568601df10a7236f","typeKey":"ApplicationShortcut_d392fa","componentTag":"citry-application-shortcut-b986f140","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
