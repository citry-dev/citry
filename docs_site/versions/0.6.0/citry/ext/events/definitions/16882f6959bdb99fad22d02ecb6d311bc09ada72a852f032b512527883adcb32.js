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
            _createElementVNode("span", {
              inert: "",
              "aria-hidden": "true",
              "data-citry-command-palette-visual": "",
              "data-citry-ui-part": "command-palette-item-start"
            }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlot35569a43fd1a2914'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot35569a43fd1a2914", { key: 0 })
                : _createCommentVNode("v-if", true)
            ]),
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs7)), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */),
            _createElementVNode("span", _mergeProps({ class: "cui-command-palette__description" }, _ctx.$citryPrepared.citryAttrs8), _toDisplayString(_ctx.$citryPrepared.citryText3), 17 /* TEXT, FULL_PROPS */),
            _createElementVNode("span", {
              inert: "",
              "aria-hidden": "true",
              "data-citry-command-palette-visual": "",
              "data-citry-ui-part": "command-palette-item-end"
            }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlotf63834e4fd50633d'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf63834e4fd50633d", { key: 1 })
                : _createCommentVNode("v-if", true)
            ])
          ], 16 /* FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs9), [
            _createElementVNode("span", {
              inert: "",
              "aria-hidden": "true",
              "data-citry-command-palette-visual": "",
              "data-citry-ui-part": "command-palette-item-start"
            }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlotf93b653098751a2e'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf93b653098751a2e", { key: 2 })
                : _createCommentVNode("v-if", true)
            ]),
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs10)), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */),
            _createElementVNode("span", _mergeProps({ class: "cui-command-palette__description" }, _ctx.$citryPrepared.citryAttrs11), _toDisplayString(_ctx.$citryPrepared.citryText5), 17 /* TEXT, FULL_PROPS */),
            _createElementVNode("span", {
              inert: "",
              "aria-hidden": "true",
              "data-citry-command-palette-visual": "",
              "data-citry-ui-part": "command-palette-item-end"
            }, [
              (_ctx.$citryPrepared.selectedSlots['citrySlot016e1997d7b818ac'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot016e1997d7b818ac", { key: 3 })
                : _createCommentVNode("v-if", true)
            ])
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot5d40b05a1c222f74", { key: 4 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 5 }, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2af52f357aadcb17dd34f1b8803e017bc3b632fc6ab222950d063a7a703be93a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-adornments" }, [
    _createElementVNode("h2", null, "Release commands with decoration"),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.open,
      onOpenChange: (value)=>_ctx.open=value,
      onAction: (value)=>_ctx.last=value,
      "citry-id": _ctx.$citryPrepared.calls.citryCall4a0c5684738e2229.id,
      key: _ctx.$citryPrepared.calls.citryCall4a0c5684738e2229.key
    }, {
      ['citrySlot35569a43fd1a2914']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__icon" }, "◆")
      ]),
      ['citrySlotf63834e4fd50633d']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__badge" }, "Beta")
      ]),
      ['citrySlotf93b653098751a2e']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__icon" }, "◆")
      ]),
      ['citrySlot016e1997d7b818ac']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__badge" }, "Beta")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "onAction", "citry-id"])),
    _createElementVNode("output", { "aria-live": "polite" }, [
      _createTextVNode("Action: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.last)
      }, "none", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fc85adf3c08985741d603ab48e5fed7598933f875472da0e894f1da90b49e46b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4a0c5684738e2229","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":126,"sourceEnd":138},{"kind":"prop","name":":onOpenChange","value":"(value)=>open=value","sourceStart":139,"sourceEnd":174},{"kind":"prop","name":":onAction","value":"(value)=>last=value","sourceStart":175,"sourceEnd":206}],"fills":[{"name":"citrySlot016e1997d7b818ac","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot35569a43fd1a2914","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf63834e4fd50633d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf93b653098751a2e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_command_adornments_1f0ae069 = _resolveComponent("citry-command-adornments-1f0ae069")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_command_adornments_1f0ae069, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2d633d749fcb2db2.id,
      key: _ctx.$citryPrepared.calls.citryCall2d633d749fcb2db2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["02e29001aca921d0b82ac5f9585d869931461f9620bad2f0b7e0ca02a821d3eb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2d633d749fcb2db2","typeKey":"CommandAdornments_81c26e","componentTag":"citry-command-adornments-1f0ae069","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
