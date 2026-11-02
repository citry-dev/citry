(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, renderList: _renderList } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
      _createElementVNode("span", { "data-citry-ui-part": "value" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
      _createElementVNode("span", {
        class: "cui-select__indicator",
        "aria-hidden": "true",
        "data-citry-ui-part": "indicator"
      })
    ], 16 /* FULL_PROPS */),
    _withDirectives(_createElementVNode("select", _mergeProps({
      class: "cui-select__native",
      "data-cui-select-native": ""
    }, _ctx.$citryPrepared.citryAttrs2), [
      _withDirectives(_createElementVNode("option", _mergeProps({ value: "" }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */), [
        [_directive_citry_vue_owned, 'selected']
      ]),
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop0, ($citryPrepared) => {
        return _withDirectives((_openBlock(), _createElementBlock("option", _normalizeProps(_guardReactiveProps($citryPrepared.citryAttrs0)), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */)), [
          [_directive_citry_vue_owned, ['selected','value']]
        ])
      }), 256 /* UNKEYED_FRAGMENT */))
    ], 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      "data-cui-select-readonly-value": ""
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-select__popup",
      popover: "manual",
      hidden: "",
      inert: "",
      "data-citry-ui-part": "popup"
    }, _ctx.$citryPrepared.citryAttrs5), [
      _createElementVNode("div", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs6)), [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop1, ($citryPrepared) => {
          return (_openBlock(), _createElementBlock(_Fragment, null, [
            ($citryPrepared.citryIf0 === 0)
              ? (_openBlock(true), _createElementBlock(_Fragment, { key: 0 }, _renderList($citryPrepared.citryLoop0, ($citryPrepared) => {
                return (_openBlock(), _createElementBlock("div", _mergeProps({
                  class: "cui-select__option",
                  role: "option",
                  "data-citry-ui-part": "option"
                }, $citryPrepared.citryAttrs0), [
                  _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "option-label" }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                  ($citryPrepared.citryIf0 === 0)
                    ? (_openBlock(), _createElementBlock("span", _mergeProps({
                      key: 0,
                      "data-citry-ui-part": "option-description"
                    }, $citryPrepared.citryAttrs2), _toDisplayString($citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */))
                    : _createCommentVNode("v-if", true)
                ], 16 /* FULL_PROPS */))
              }), 256 /* UNKEYED_FRAGMENT */))
              : ($citryPrepared.citryIf0 === 1)
                ? (_openBlock(), _createElementBlock("div", _mergeProps({
                  key: 1,
                  class: "cui-select__group",
                  role: "group",
                  "data-citry-ui-part": "group"
                }, $citryPrepared.citryAttrs0), [
                  _createElementVNode("span", _mergeProps({
                    class: "cui-select__group-label",
                    "data-citry-ui-part": "group-label"
                  }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($citryPrepared.citryLoop1, ($citryPrepared) => {
                    return (_openBlock(), _createElementBlock("div", _mergeProps({
                      class: "cui-select__option",
                      role: "option",
                      "data-citry-ui-part": "option"
                    }, $citryPrepared.citryAttrs0), [
                      _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "option-label" }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                      ($citryPrepared.citryIf0 === 0)
                        ? (_openBlock(), _createElementBlock("span", _mergeProps({
                          key: 0,
                          "data-citry-ui-part": "option-description"
                        }, $citryPrepared.citryAttrs2), _toDisplayString($citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */))
                        : _createCommentVNode("v-if", true)
                    ], 16 /* FULL_PROPS */))
                  }), 256 /* UNKEYED_FRAGMENT */))
                ], 16 /* FULL_PROPS */))
              : _createCommentVNode("v-if", true)
          ], 64 /* STABLE_FRAGMENT */))
        }), 256 /* UNKEYED_FRAGMENT */))
      ], 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e79ab0f686775c933f4883abb1db1cea884f88f274e6b5c50ab6fdccfba38ef4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      _createElementVNode("span", {
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, " * ")
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["16cda6cc549682aec61a8b482e9e07b2c080fc7f48abe0572d16d6759b2e8b52"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_select_6ddf7482 = _resolveComponent("citry-c-select-6ddf7482")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("form", {
    onSubmit: _withModifiers($event => (_ctx.result = Array.from(new window.FormData($event.target).entries())), ["prevent"])
  }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1b28502375ffd01f.id,
      key: _ctx.$citryPrepared.calls.citryCall1b28502375ffd01f.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Review status")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_select_6ddf7482, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall64e57d7676ffbdde.id,
          key: _ctx.$citryPrepared.calls.citryCall64e57d7676ffbdde.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2beade08a77a37a8.id,
      key: _ctx.$citryPrepared.calls.citryCall2beade08a77a37a8.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Save")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall803999b994fdbbbf.id,
      key: _ctx.$citryPrepared.calls.citryCall803999b994fdbbbf.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Reset")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(JSON.stringify(_ctx.result))
    }, null, 8 /* PROPS */, ["textContent"])
  ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["475018babff0ad73f8814a1e241f7e08df76db958f8829fc057e8c9099db5e46"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall64e57d7676ffbdde","typeKey":"CSelect_005ed0","componentTag":"citry-c-select-6ddf7482","bindings":[]},{"localId":"citryCall1b28502375ffd01f","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall64e57d7676ffbdde"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2beade08a77a37a8","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall803999b994fdbbbf","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_select_form_5c3b0fd2 = _resolveComponent("citry-select-form-5c3b0fd2")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_select_form_5c3b0fd2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallde5f07cc1f5efea7.id,
      key: _ctx.$citryPrepared.calls.citryCallde5f07cc1f5efea7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb1242d487df36932a207f89808a963a191368bf8e1c3dbea9928ec975309a5c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallde5f07cc1f5efea7","typeKey":"SelectForm_4fc306","componentTag":"citry-select-form-5c3b0fd2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
