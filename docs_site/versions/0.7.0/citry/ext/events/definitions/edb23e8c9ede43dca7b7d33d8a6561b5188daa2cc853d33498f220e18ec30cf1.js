(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
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
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
          _createElementVNode("span", { "data-citry-ui-part": "option-description" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs8)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
          _createElementVNode("span", { "data-citry-ui-part": "option-description" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs9)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
          _createElementVNode("span", { "data-citry-ui-part": "option-description" }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("li", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs10)), [
          _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */),
          _createElementVNode("span", { "data-citry-ui-part": "option-description" }, _toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "loading"
      }, _ctx.$citryPrepared.citryAttrs11), [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-combobox__status",
        role: "status",
        "data-citry-ui-part": "empty"
      }, _ctx.$citryPrepared.citryAttrs12), [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", {
        class: "cui-combobox__status cui-combobox__status--error",
        role: "status",
        "data-citry-ui-part": "error"
      }, [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ef5986d67827b467acf44f9e3fd809629937fcf650fafe64af5073ee6175aed9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fcec8560113f1cb2757bbacf9b66e82df47bdaac4eb43c0ce5bffdb59636c061"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_combobox_4720d729 = _resolveComponent("citry-c-combobox-4720d729")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createElementBlock("section", { class: "deep-sky-theme" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Deep-sky palette"),
      _createElementVNode("h2", null, "Search the Messier catalog")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall62037f88ffa5ff2d.id,
      key: _ctx.$citryPrepared.calls.citryCall62037f88ffa5ff2d.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode(" Messier object ")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_combobox_4720d729, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall67c230090a9fbc52.id,
          key: _ctx.$citryPrepared.calls.citryCall67c230090a9fbc52.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0ceee59395a954586e3ae6230517842d65ed832934ab05aecdc8acada6bd1109"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall67c230090a9fbc52","typeKey":"CCombobox_bdcbb7","componentTag":"citry-c-combobox-4720d729","bindings":[]},{"localId":"citryCall62037f88ffa5ff2d","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall67c230090a9fbc52"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_deep_sky_theme_816dde13 = _resolveComponent("citry-deep-sky-theme-816dde13")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_deep_sky_theme_816dde13, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla6d5313238d183a8.id,
      key: _ctx.$citryPrepared.calls.citryCalla6d5313238d183a8.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bc10f833905bd93d86839d8a65fce252941fbc1c44afa66ce27ae884ffd030f7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla6d5313238d183a8","typeKey":"DeepSkyTheme_e4ca9b","componentTag":"citry-deep-sky-theme-816dde13","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
