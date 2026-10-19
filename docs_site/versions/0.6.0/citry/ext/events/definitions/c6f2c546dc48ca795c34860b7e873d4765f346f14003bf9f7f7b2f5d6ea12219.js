(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, renderList: _renderList } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("button", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
      _createElementVNode("span", {
        class: "cui-multi-select__values",
        "data-citry-ui-part": "values"
      }, [
        (_ctx.$citryPrepared.citryIf0 === 0)
          ? (_openBlock(), _createElementBlock("span", {
            key: 0,
            "data-citry-ui-part": "placeholder"
          }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */))
          : _createCommentVNode("v-if", true),
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop0, ($citryPrepared) => {
          return (_openBlock(), _createElementBlock("span", _mergeProps({
            class: "cui-multi-select__chip",
            "data-citry-ui-part": "chip"
          }, $citryPrepared.citryAttrs0), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */))
        }), 256 /* UNKEYED_FRAGMENT */))
      ]),
      _createElementVNode("span", {
        class: "cui-multi-select__indicator",
        "aria-hidden": "true",
        "data-citry-ui-part": "indicator"
      })
    ], 16 /* FULL_PROPS */),
    _withDirectives(_createElementVNode("select", _mergeProps({
      class: "cui-multi-select__native",
      multiple: "",
      "data-cui-multi-select-native": ""
    }, _ctx.$citryPrepared.citryAttrs2), [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop1, ($citryPrepared) => {
        return _withDirectives((_openBlock(), _createElementBlock("option", _normalizeProps(_guardReactiveProps($citryPrepared.citryAttrs0)), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */)), [
          [_directive_citry_vue_owned, ['selected','value']]
        ])
      }), 256 /* UNKEYED_FRAGMENT */))
    ], 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ]),
    _createElementVNode("span", {
      hidden: "",
      "data-cui-multi-select-readonly-values": ""
    }, [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop2, ($citryPrepared) => {
        return _withDirectives((_openBlock(), _createElementBlock("input", _mergeProps({ type: "hidden" }, $citryPrepared.citryAttrs0), null, 16 /* FULL_PROPS */)), [
          [_directive_citry_vue_owned, 'value']
        ])
      }), 256 /* UNKEYED_FRAGMENT */))
    ]),
    _createElementVNode("div", _mergeProps({
      class: "cui-multi-select__popup",
      popover: "manual",
      hidden: "",
      inert: "",
      "data-citry-ui-part": "popup"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("div", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop3, ($citryPrepared) => {
          return (_openBlock(), _createElementBlock(_Fragment, null, [
            ($citryPrepared.citryIf0 === 0)
              ? (_openBlock(true), _createElementBlock(_Fragment, { key: 1 }, _renderList($citryPrepared.citryLoop0, ($citryPrepared) => {
                return (_openBlock(), _createElementBlock("div", _mergeProps({
                  class: "cui-multi-select__option",
                  role: "option",
                  "data-citry-ui-part": "option"
                }, $citryPrepared.citryAttrs0), [
                  _createElementVNode("span", {
                    class: "cui-multi-select__check",
                    "aria-hidden": "true"
                  }),
                  _createElementVNode("span", null, [
                    _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "option-label" }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                    ($citryPrepared.citryIf0 === 0)
                      ? (_openBlock(), _createElementBlock("span", _mergeProps({
                        key: 0,
                        "data-citry-ui-part": "option-description"
                      }, $citryPrepared.citryAttrs2), _toDisplayString($citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */))
                      : _createCommentVNode("v-if", true)
                  ])
                ], 16 /* FULL_PROPS */))
              }), 256 /* UNKEYED_FRAGMENT */))
              : ($citryPrepared.citryIf0 === 1)
                ? (_openBlock(), _createElementBlock("div", _mergeProps({
                  key: 2,
                  class: "cui-multi-select__group",
                  role: "group",
                  "data-citry-ui-part": "group"
                }, $citryPrepared.citryAttrs0), [
                  _createElementVNode("span", _mergeProps({
                    class: "cui-multi-select__group-label",
                    "data-citry-ui-part": "group-label"
                  }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($citryPrepared.citryLoop1, ($citryPrepared) => {
                    return (_openBlock(), _createElementBlock("div", _mergeProps({
                      class: "cui-multi-select__option",
                      role: "option",
                      "data-citry-ui-part": "option"
                    }, $citryPrepared.citryAttrs0), [
                      _createElementVNode("span", {
                        class: "cui-multi-select__check",
                        "aria-hidden": "true"
                      }),
                      _createElementVNode("span", null, [
                        _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "option-label" }, $citryPrepared.citryAttrs1), _toDisplayString($citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
                        ($citryPrepared.citryIf0 === 0)
                          ? (_openBlock(), _createElementBlock("span", _mergeProps({
                            key: 0,
                            "data-citry-ui-part": "option-description"
                          }, $citryPrepared.citryAttrs2), _toDisplayString($citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */))
                          : _createCommentVNode("v-if", true)
                      ])
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e6b659e9dcd0cfe2aab9421454085841c4435b4b2cc723f63feedcb4ef295699"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a58a56567942056fa7cc146807ca9cf3d10f886357d48bc5c3c148f184bbba7f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_multi_select_4f943335 = _resolveComponent("citry-c-multi-select-4f943335")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("form", {
    onSubmit: _withModifiers($event => (_ctx.result = Array.from(new window.FormData($event.target).entries())), ["prevent"])
  }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall725a80d10f5937c4.id,
      key: _ctx.$citryPrepared.calls.citryCall725a80d10f5937c4.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Reviewers")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_multi_select_4f943335, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalleb4bdeebfcc316a3.id,
          key: _ctx.$citryPrepared.calls.citryCalleb4bdeebfcc316a3.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallce201e8bfc797c8c.id,
      key: _ctx.$citryPrepared.calls.citryCallce201e8bfc797c8c.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Save")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5042345613246d7a.id,
      key: _ctx.$citryPrepared.calls.citryCall5042345613246d7a.key
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c236b847f64e46b392de2d85c9778da7055c38135d7f469149c1a07fecca5fc6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalleb4bdeebfcc316a3","typeKey":"CMultiSelect_e37e33","componentTag":"citry-c-multi-select-4f943335","bindings":[]},{"localId":"citryCall725a80d10f5937c4","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCalleb4bdeebfcc316a3"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallce201e8bfc797c8c","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5042345613246d7a","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_multi_select_form_1dfd4c40 = _resolveComponent("citry-multi-select-form-1dfd4c40")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_multi_select_form_1dfd4c40, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall335c0a1be8f704d7.id,
      key: _ctx.$citryPrepared.calls.citryCall335c0a1be8f704d7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2c374d10057766a3b481b44d23f459abb50e06c6f4ec2b4afbd651b3c5364a77"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall335c0a1be8f704d7","typeKey":"MultiSelectForm_7dcd6c","componentTag":"citry-multi-select-form-1dfd4c40","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
