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
              (_ctx.$citryPrepared.selectedSlots['citrySlotc9d1cbd38c4a6e77'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotc9d1cbd38c4a6e77", { key: 0 })
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
              (_ctx.$citryPrepared.selectedSlots['citrySlotf0acd1bb6e733e91'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf0acd1bb6e733e91", { key: 1 })
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
              (_ctx.$citryPrepared.selectedSlots['citrySlot099b4e4607d26230'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot099b4e4607d26230", { key: 2 })
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
              (_ctx.$citryPrepared.selectedSlots['citrySlote8f9216d1b5f3b6c'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlote8f9216d1b5f3b6c", { key: 3 })
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
          (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot2b1da198118e4ee7", { key: 4 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 5 }, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["41c2a2aa959494918873b38827436241e380b6b49d1e8f246251b3a78d54f2d7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      "citry-id": _ctx.$citryPrepared.calls.citryCall965250f03b456d0e.id,
      key: _ctx.$citryPrepared.calls.citryCall965250f03b456d0e.key
    }, {
      ['citrySlotc9d1cbd38c4a6e77']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__icon" }, "◆")
      ]),
      ['citrySlotf0acd1bb6e733e91']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__badge" }, "Beta")
      ]),
      ['citrySlot099b4e4607d26230']: _withCtx(() => [
        _createElementVNode("span", { class: "command-palette-adornments__icon" }, "◆")
      ]),
      ['citrySlote8f9216d1b5f3b6c']: _withCtx(() => [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["90e479f4b9815a3a758103b9c2095a7932a097d241d6be1f5c0c39f1bd4bf34c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall965250f03b456d0e","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":126,"sourceEnd":138},{"kind":"prop","name":":onOpenChange","value":"(value)=>open=value","sourceStart":139,"sourceEnd":174},{"kind":"prop","name":":onAction","value":"(value)=>last=value","sourceStart":175,"sourceEnd":206}],"fills":[{"name":"citrySlot099b4e4607d26230","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc9d1cbd38c4a6e77","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote8f9216d1b5f3b6c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotf0acd1bb6e733e91","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_command_adornments_f7840031 = _resolveComponent("citry-command-adornments-f7840031")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_command_adornments_f7840031, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall25c0a40b128c2358.id,
      key: _ctx.$citryPrepared.calls.citryCall25c0a40b128c2358.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["12f028118d4612f4caa29111c039b4167b96f9bfcfc1954a8f896d03ed27e7ba"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall25c0a40b128c2358","typeKey":"CommandAdornments_242f79","componentTag":"citry-command-adornments-f7840031","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
