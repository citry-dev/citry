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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_multi_select_4f943335 = _resolveComponent("citry-c-multi-select-4f943335")
  
  return (_openBlock(), _createElementBlock("div", null, [
    (_openBlock(), _createBlock(_component_citry_c_multi_select_4f943335, {
      value: _ctx.value,
      onValueChange: (next) => _ctx.value = next,
      "citry-id": _ctx.$citryPrepared.calls.citryCall5399db4d362bca22.id,
      key: _ctx.$citryPrepared.calls.citryCall5399db4d362bca22.key
    }, null, 8 /* PROPS */, ["value", "onValueChange", "citry-id"])),
    _createElementVNode("p", null, [
      _createTextVNode("Current: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.value.join(', '))
      }, null, 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["450b42c6f202a93cb014a597bbf8591e792c4a75edfdf6f4afe98180b3e9af44"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5399db4d362bca22","typeKey":"CMultiSelect_e37e33","componentTag":"citry-c-multi-select-4f943335","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":40,"sourceEnd":54},{"kind":"prop","name":":onValueChange","value":"(next) => value = next","sourceStart":55,"sourceEnd":94}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_multi_select_af694f8c = _resolveComponent("citry-controlled-multi-select-af694f8c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_multi_select_af694f8c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall3260de4a0278210d.id,
      key: _ctx.$citryPrepared.calls.citryCall3260de4a0278210d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6978a5d8fe6e16e5c7831ddf25d69e5d0bd1543c0381b878512f5ebe1617d547"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3260de4a0278210d","typeKey":"ControlledMultiSelect_6b7bdf","componentTag":"citry-controlled-multi-select-af694f8c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
