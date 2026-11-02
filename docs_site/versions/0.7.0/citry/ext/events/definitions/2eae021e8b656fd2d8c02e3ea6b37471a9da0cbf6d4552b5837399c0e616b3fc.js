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
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-command-palette-host",
    "data-citry-command-palette-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot1ab9ff8634c60b97'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot1ab9ff8634c60b97", { key: 0 })
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
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot2b1da198118e4ee7", { key: 1 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot2b1da198118e4ee7'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 2 }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ec4d6a2675981e127586535e18ea364761ff3e795ebdfb15caecebb4c27e07b7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-popover-host",
    "data-citry-popover-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot371618f8b14ff656'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot371618f8b14ff656", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-popover",
      popover: "manual",
      role: "dialog",
      tabindex: "-1",
      "data-citry-ui-part": "popover"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("header", {
        class: "cui-popover__header",
        "data-citry-ui-part": "header"
      }, [
        _createElementVNode("h2", _mergeProps({
          class: "cui-popover__title",
          "data-citry-ui-part": "title"
        }, _ctx.$citryPrepared.citryAttrs1), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot6797d7221c481487'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot6797d7221c481487", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ]),
      _createElementVNode("div", {
        class: "cui-popover__body",
        "data-citry-ui-part": "body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot324bf05fa215c365'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot324bf05fa215c365", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2b649a5f47d1d9e8e1b8f057ac12e41dfe825104ddb7610df5fe7acaa7676ffe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot01f533d219338d4d'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot01f533d219338d4d", { key: 0 })
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot81c7ca490fc15941'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot81c7ca490fc15941", { key: 1 })
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
          (_ctx.$citryPrepared.selectedSlots['citrySlotc18de8dd8e2a7fea'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotc18de8dd8e2a7fea", { key: 2 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5e2dd78f13abf7a18d27832b188ba4399e862b02a5aca2f4016750784213bc22"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  const _component_citry_c_popover_e1fe086e = _resolveComponent("citry-c-popover-e1fe086e")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-layers" }, [
    _createElementVNode("h2", null, "Modal and anchored layers"),
    (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallba4736186c4eb2be.id,
      key: _ctx.$citryPrepared.calls.citryCallba4736186c4eb2be.key
    }, {
      ['citrySlot01f533d219338d4d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallad26d6feaaa4882c.id,
          key: _ctx.$citryPrepared.calls.citryCallad26d6feaaa4882c.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Open deployment workflow")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot81c7ca490fc15941']: _withCtx(() => [
        _createTextVNode("Deployment workflow")
      ]),
      ['citrySlotc18de8dd8e2a7fea']: _withCtx(() => [
        _createElementVNode("div", { class: "command-palette-layers__workflow" }, [
          _createElementVNode("div", { ref: "paletteOwner" }, [
            (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
              open: _ctx.paletteOpen,
              onOpenChange: (value) => _ctx.paletteOpen = value,
              onAction: _ctx.handlePaletteAction,
              "citry-id": _ctx.$citryPrepared.calls.citryCall9daa3b69c7c01f93.id,
              key: _ctx.$citryPrepared.calls.citryCall9daa3b69c7c01f93.key
            }, {
              ['citrySlot1ab9ff8634c60b97']: _withCtx(() => [
                (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
                  "citry-id": _ctx.$citryPrepared.calls.citryCall6df4319aaad16f93.id,
                  key: _ctx.$citryPrepared.calls.citryCall6df4319aaad16f93.key
                }, {
                  ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                    _createTextVNode("Open workflow commands")
                  ]),
                  _: 2 /* DYNAMIC */
                }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "onAction", "citry-id"]))
          ], 512 /* NEED_PATCH */),
          (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
            open: _ctx.popoverOpen,
            onOpenChange: (value) => _ctx.popoverOpen = value,
            "citry-id": _ctx.$citryPrepared.calls.citryCallc11142b66b207634.id,
            key: _ctx.$citryPrepared.calls.citryCallc11142b66b207634.key
          }, {
            ['citrySlot371618f8b14ff656']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall716e73108d5a028d.id,
                key: _ctx.$citryPrepared.calls.citryCall716e73108d5a028d.key
              }, {
                ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                  _createTextVNode("Details anchor")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            ['citrySlot6797d7221c481487']: _withCtx(() => [
              _createTextVNode("Deployment details")
            ]),
            ['citrySlot324bf05fa215c365']: _withCtx(() => [
              _createTextVNode("The latest deployment passed its checks.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "onOpenChange", "citry-id"])),
          _withDirectives(_createElementVNode("button", {
            key: "citryReplacementd062c2ec796c1234d8af5c6645c6bdcb2641879522910bc27f50faaa460f3479",
            type: "button",
            onClick: _ctx.removePaletteOwner
          }, " Remove palette owner ", 8 /* PROPS */, ["onClick"]), [
            [_vShow, !_ctx.removed]
          ]),
          _createElementVNode("output", {
            textContent: _toDisplayString(_ctx.removed ? 'Palette owner removed' : 'Palette owner present')
          }, " Palette owner present ", 8 /* PROPS */, ["textContent"])
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", {
      ref: "shadowHost",
      class: "command-palette-layers__shadow-host"
    }, [
      _createElementVNode("div", { ref: "shadowFixture" }, [
        (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallc8c02c9ec311a372.id,
          key: _ctx.$citryPrepared.calls.citryCallc8c02c9ec311a372.key
        }, {
          ['citrySlot1ab9ff8634c60b97']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall9c90732480f1582a.id,
              key: _ctx.$citryPrepared.calls.citryCall9c90732480f1582a.key
            }, {
              ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                _createTextVNode("Open ShadowRoot fixture")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ], 512 /* NEED_PATCH */)
    ], 512 /* NEED_PATCH */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a3b0d1c4638f26b89e276d063d90a61826160e02b099af724cf5ed9eaeeadfc9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivecf39e6fb88049349eb60556ec7b6a4f406493d89a7dd6f8ea02fd611f06f918bD1","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectivecf39e6fb88049349eb60556ec7b6a4f406493d89a7dd6f8ea02fd611f06f918b","replacementKey":"citryReplacementd062c2ec796c1234d8af5c6645c6bdcb2641879522910bc27f50faaa460f3479","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCallad26d6feaaa4882c","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6df4319aaad16f93","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9daa3b69c7c01f93","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"paletteOpen","sourceStart":804,"sourceEnd":823},{"kind":"prop","name":":onOpenChange","value":"(value) => paletteOpen = value","sourceStart":824,"sourceEnd":870},{"kind":"prop","name":":onAction","value":"handlePaletteAction","sourceStart":871,"sourceEnd":902}],"fills":[{"name":"citrySlot1ab9ff8634c60b97","localDescendants":["citryCall6df4319aaad16f93"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall716e73108d5a028d","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc11142b66b207634","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[{"kind":"prop","name":":open","value":"popoverOpen","sourceStart":1446,"sourceEnd":1465},{"kind":"prop","name":":onOpenChange","value":"(value) => popoverOpen = value","sourceStart":1466,"sourceEnd":1512}],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCall716e73108d5a028d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallba4736186c4eb2be","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot01f533d219338d4d","localDescendants":["citryCallad26d6feaaa4882c"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot81c7ca490fc15941","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc18de8dd8e2a7fea","localDescendants":["citryCall6df4319aaad16f93","citryCall716e73108d5a028d","citryCall9daa3b69c7c01f93","citryCallc11142b66b207634"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9c90732480f1582a","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc8c02c9ec311a372","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[],"fills":[{"name":"citrySlot1ab9ff8634c60b97","localDescendants":["citryCall9c90732480f1582a"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_palette_layers_37804bae = _resolveComponent("citry-palette-layers-37804bae")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_palette_layers_37804bae, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2be3f08bf5e7ccbb.id,
      key: _ctx.$citryPrepared.calls.citryCall2be3f08bf5e7ccbb.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f5b281ec57aa2bf42e184efda65e6b9a3d421af130fd20124da05775fd7cd8d1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2be3f08bf5e7ccbb","typeKey":"PaletteLayers_cbe09e","componentTag":"citry-palette-layers-37804bae","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
