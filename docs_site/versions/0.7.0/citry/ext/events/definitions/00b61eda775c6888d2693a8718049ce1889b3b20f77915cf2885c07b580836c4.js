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
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a5c3b89119e24e0edb50b0c4d8146aa09a3101e367fac6a368ec0e1841947dcf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_select_6ddf7482 = _resolveComponent("citry-c-select-6ddf7482")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallfb3c847282184b30.id,
    key: _ctx.$citryPrepared.calls.citryCallfb3c847282184b30.key
  }, {
    ['citrySlote2526e6f745e4169']: _withCtx(() => [
      _createTextVNode("Workspace")
    ]),
    ['citrySlot6f90e269deb4619c']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_select_6ddf7482, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf998a91bc8ea5ea1.id,
        key: _ctx.$citryPrepared.calls.citryCallf998a91bc8ea5ea1.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    ['citrySlote7646b39489ca911']: _withCtx(() => [
      _createTextVNode("Choose where new observations belong.")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["60577a40d5f4fbe490efa532a139add6622c75bc06a30cd72e7664a038a20a02"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf998a91bc8ea5ea1","typeKey":"CSelect_005ed0","componentTag":"citry-c-select-6ddf7482","bindings":[]},{"localId":"citryCallfb3c847282184b30","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCallf998a91bc8ea5ea1"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_select_at_a_glance_1728b1a5 = _resolveComponent("citry-select-at-a-glance-1728b1a5")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_select_at_a_glance_1728b1a5, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6319eec271deb0c7.id,
      key: _ctx.$citryPrepared.calls.citryCall6319eec271deb0c7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2354afa278befb363823b8ef3412fd04455aa19ed1853ca08ae0a177df160db0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6319eec271deb0c7","typeKey":"SelectAtAGlance_4ec61e","componentTag":"citry-select-at-a-glance-1728b1a5","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
