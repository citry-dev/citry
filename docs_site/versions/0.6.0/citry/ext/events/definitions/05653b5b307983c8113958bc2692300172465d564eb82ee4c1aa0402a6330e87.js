(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-combobox",
    "data-citry-combobox-root": "",
    "data-citry-ui-part": "root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-combobox__control",
      "data-citry-ui-part": "control"
    }, [
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-combobox__input",
        type: "text",
        role: "combobox",
        "aria-autocomplete": "list",
        readonly: "",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ]),
      _createElementVNode("button", _mergeProps({
        class: "cui-combobox__clear",
        type: "button",
        tabindex: "-1",
        "data-citry-combobox-clear": "",
        "data-citry-ui-part": "clear"
      }, _ctx.$citryPrepared.citryAttrs2), [
        _createElementVNode("span", { "aria-hidden": "true" }, " × ")
      ], 16 /* FULL_PROPS */),
      _createElementVNode("button", _mergeProps({
        class: "cui-combobox__trigger",
        type: "button",
        "aria-haspopup": "listbox",
        tabindex: "-1",
        "data-citry-combobox-trigger": "",
        "data-citry-ui-part": "trigger"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", { "aria-hidden": "true" }, " ▾ ")
      ], 16 /* FULL_PROPS */)
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      "data-citry-combobox-form-value": ""
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-combobox__popup",
      "data-citry-ui-part": "popup"
    }, _ctx.$citryPrepared.citryAttrs5), [
      _createElementVNode("ul", _mergeProps({
        class: "cui-combobox__listbox",
        role: "listbox",
        "data-citry-ui-part": "listbox"
      }, _ctx.$citryPrepared.citryAttrs6), [
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs7)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs8)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs9)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "loading"
      }, _ctx.$citryPrepared.citryAttrs10), [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "empty"
      }, _ctx.$citryPrepared.citryAttrs11), [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", {
        class: "cui-combobox__status cui-combobox__status--error",
        role: "status",
        "data-citry-ui-part": "error"
      }, [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3c4f7fe70be0690a37cb4004e7bfa80753dc2fd8cdebf3d8cfaabcb04233e6e6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot39e9540beec747a3'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot39e9540beec747a3", { key: 0 })
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f4d122daf10cdd'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f4d122daf10cdd", { key: 1 })
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
        _createElementVNode("div", _mergeProps({
          class: "cui-dialog__description",
          "data-citry-ui-part": "description"
        }, _ctx.$citryPrepared.citryAttrs3), [
          (_ctx.$citryPrepared.selectedSlots['citrySlotc675106427a13a6b'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotc675106427a13a6b", { key: 2 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot4c119cf029159074'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot4c119cf029159074", { key: 3 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["498553432d08027fae7b783e98b47caa07a2d23f0ec0071addc109910acc3630"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-658ac8ee869944a7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "header" }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("div", { class: "cui-card__header-content" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot9447b0af7804e094'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot9447b0af7804e094", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", {
      class: "cui-card__body",
      "data-citry-ui-part": "body"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotde2ab6e38bf88e32'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotde2ab6e38bf88e32", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "footer" }, _ctx.$citryPrepared.citryAttrs2), [
      _createElementVNode("div", {
        class: "cui-card__actions",
        "data-citry-ui-part": "actions"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot061e674a761e49ea'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot061e674a761e49ea", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["701b460146226c2844d89c16a9bbd1df685aeebecf278426660412d3edb84595"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-658ac8ee869944a7","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-658ac8ee869944a7","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_combobox_4720d729 = _resolveComponent("citry-c-combobox-4720d729")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  const _component_citry_c_card_f6be905a = _resolveComponent("citry-c-card-f6be905a")
  
  return (_openBlock(), _createElementBlock("section", { class: "card-nested" }, [
    (_openBlock(), _createBlock(_component_citry_c_card_f6be905a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla27d0de01be2b561.id,
      key: _ctx.$citryPrepared.calls.citryCalla27d0de01be2b561.key
    }, {
      ['citrySlot9447b0af7804e094']: _withCtx(() => [
        _createElementVNode("h2", null, "Place the reading chair")
      ]),
      ['citrySlotde2ab6e38bf88e32']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallfbceaabd0f6dd9f6.id,
          key: _ctx.$citryPrepared.calls.citryCallfbceaabd0f6dd9f6.key
        }, {
          ['citrySlote2526e6f745e4169']: _withCtx(() => [
            _createTextVNode("Room")
          ]),
          ['citrySlot6f90e269deb4619c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_combobox_4720d729, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallf39ce9252943ad58.id,
              key: _ctx.$citryPrepared.calls.citryCallf39ce9252943ad58.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot061e674a761e49ea']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall162036a37bd8fda9.id,
          key: _ctx.$citryPrepared.calls.citryCall162036a37bd8fda9.key
        }, {
          ['citrySlot39e9540beec747a3']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall145750e26c6d65f2.id,
              key: _ctx.$citryPrepared.calls.citryCall145750e26c6d65f2.key
            }, {
              ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                _createTextVNode(" Check dimensions ")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
            _createTextVNode("Reading chair dimensions")
          ]),
          ['citrySlotc675106427a13a6b']: _withCtx(() => [
            _createTextVNode(" Measure doorways and the chosen corner before delivery. ")
          ]),
          ['citrySlot4c119cf029159074']: _withCtx(() => [
            _createTextVNode(" The chair is 76 cm wide, 84 cm deep, and 92 cm tall. ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["07e82eed1e531876c51404f567a1b1b5a96cb756987d575a009d14e3f1596aac"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf39ce9252943ad58","typeKey":"CCombobox_bdcbb7","componentTag":"citry-c-combobox-4720d729","bindings":[]},{"localId":"citryCallfbceaabd0f6dd9f6","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCallf39ce9252943ad58"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall145750e26c6d65f2","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall162036a37bd8fda9","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCall145750e26c6d65f2"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc675106427a13a6b","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla27d0de01be2b561","typeKey":"CCard_19daae","componentTag":"citry-c-card-f6be905a","bindings":[],"fills":[{"name":"citrySlot061e674a761e49ea","localDescendants":["citryCall145750e26c6d65f2","citryCall162036a37bd8fda9"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9447b0af7804e094","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotde2ab6e38bf88e32","localDescendants":["citryCallf39ce9252943ad58","citryCallfbceaabd0f6dd9f6"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_card_nested_content_66001ca6 = _resolveComponent("citry-card-nested-content-66001ca6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_card_nested_content_66001ca6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9e9a505a9a868bee.id,
      key: _ctx.$citryPrepared.calls.citryCall9e9a505a9a868bee.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6d3ab3ce9503626bda6ee9158245e7c451304be0690ff3a43fd0a9ab07da6241"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9e9a505a9a868bee","typeKey":"CardNestedContent_d4ddad","componentTag":"citry-card-nested-content-66001ca6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
