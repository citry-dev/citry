(function(Vue){

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return null
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c450ca7b6b11935f61db776d24be03f05867ed3e567cda5b6767f4af1f6d2417"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-cascader",
    "data-citry-ui-part": "cascader"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("button", _mergeProps({
      type: "button",
      "aria-haspopup": "tree",
      "data-citry-ui-part": "trigger"
    }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("span", { "data-citry-ui-part": "value" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
      _createElementVNode("span", {
        "aria-hidden": "true",
        "data-citry-ui-part": "indicator"
      }, "⌄")
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "popup" }, _ctx.$citryPrepared.citryAttrs2), [
      _createElementVNode("ul", _mergeProps({
        role: "tree",
        "data-citry-cascader-column": "",
        "data-level": "1",
        "data-citry-ui-part": "tree"
      }, _ctx.$citryPrepared.citryAttrs3), [
        (true)
          ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.citryKey0 }, [
            (_openBlock(), _createElementBlock("li", _mergeProps({ "data-citry-ui-part": "option" }, _ctx.$citryPrepared.citryAttrs4, { key: _ctx.$citryPrepared.citryKey1 }), [
              _createElementVNode("div", { "data-citry-ui-part": "option-row" }, [
                _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
                _createElementVNode("span", {
                  "aria-hidden": "true",
                  "data-citry-ui-part": "option-indicator"
                }, "›")
              ])
            ], 16 /* FULL_PROPS */)),
            (false)
              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, null, 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 64 /* STABLE_FRAGMENT */))
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      (true)
        ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.citryKey2 }, [
          _createElementVNode("ul", _mergeProps({
            role: "group",
            "data-citry-cascader-column": "",
            "data-citry-ui-part": "group"
          }, _ctx.$citryPrepared.citryAttrs5), [
            (true)
              ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.citryKey3 }, [
                (_openBlock(), _createElementBlock("li", _mergeProps({ "data-citry-ui-part": "option" }, _ctx.$citryPrepared.citryAttrs6, { key: _ctx.$citryPrepared.citryKey4 }), [
                  _createElementVNode("div", { "data-citry-ui-part": "option-row" }, [
                    _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
                    _createElementVNode("span", {
                      "aria-hidden": "true",
                      "data-citry-ui-part": "option-indicator"
                    }, "›")
                  ])
                ], 16 /* FULL_PROPS */)),
                (false)
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, null, 64 /* STABLE_FRAGMENT */))
                  : _createCommentVNode("v-if", true)
              ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          (false)
            ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, null, 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ], 64 /* STABLE_FRAGMENT */))
        : _createCommentVNode("v-if", true),
      (true)
        ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.citryKey5 }, [
          _createElementVNode("ul", _mergeProps({
            role: "group",
            "data-citry-cascader-column": "",
            "data-citry-ui-part": "group"
          }, _ctx.$citryPrepared.citryAttrs7), [
            (true)
              ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.citryKey6 }, [
                (_openBlock(), _createElementBlock("li", _mergeProps({ "data-citry-ui-part": "option" }, _ctx.$citryPrepared.citryAttrs8, { key: _ctx.$citryPrepared.citryKey7 }), [
                  _createElementVNode("div", { "data-citry-ui-part": "option-row" }, [
                    _createElementVNode("span", { "data-citry-ui-part": "option-label" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                  ])
                ], 16 /* FULL_PROPS */)),
                (false)
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, null, 64 /* STABLE_FRAGMENT */))
                  : _createCommentVNode("v-if", true)
              ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          (false)
            ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, null, 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ], 64 /* STABLE_FRAGMENT */))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      "data-citry-ui-part": "inputs",
      hidden: ""
    }, [
      _withDirectives(_createElementVNode("input", _mergeProps({ type: "hidden" }, _ctx.$citryPrepared.citryAttrs9), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({ type: "hidden" }, _ctx.$citryPrepared.citryAttrs10), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({ type: "hidden" }, _ctx.$citryPrepared.citryAttrs11), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ])
    ]),
    _createElementVNode("span", {
      hidden: "",
      "aria-hidden": "true"
    }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
    _createElementVNode("span", {
      hidden: "",
      "aria-hidden": "true"
    }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */),
    _createElementVNode("span", {
      "data-citry-ui-part": "status",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true"
    }, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9b4b8c6113bb6905e027a48f97e62e2a941d054ca510edd5dc8232f7e3d0d312"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, renderSlot: _renderSlot, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_internal_cascader_1a954eba = _resolveComponent("citry-c-internal-cascader-1a954eba")
  
  return (_openBlock(), _createElementBlock(_Fragment, null, [
    (_ctx.$citryPrepared.selectedSlots['citrySlotfd0d5223a93ec546'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotfd0d5223a93ec546", { key: 0 })
      : _createCommentVNode("v-if", true),
    (_openBlock(), _createBlock(_component_citry_c_internal_cascader_1a954eba, {
      ref: "root",
      "citry-id": _ctx.$citryPrepared.calls.citryCall929a734ed9f00e01.id,
      key: _ctx.$citryPrepared.calls.citryCall929a734ed9f00e01.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ], 64 /* STABLE_FRAGMENT */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["954c80ce42fc5afb8c0501bfa57bb8c070dd6e41cd9a8e5a7c9b40b83cfbc98c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall929a734ed9f00e01","typeKey":"CInternalCascader_765093","componentTag":"citry-c-internal-cascader-1a954eba","bindings":[{"kind":"ref-static","name":"ref","value":"root","sourceStart":164,"sourceEnd":174}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_cascader_option_17b40f7e = _resolveComponent("citry-c-cascader-option-17b40f7e")
  const _component_citry_c_cascader_06b92651 = _resolveComponent("citry-c-cascader-06b92651")
  
  return (_openBlock(), _createElementBlock("form", null, [
    (_openBlock(), _createBlock(_component_citry_c_cascader_06b92651, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall00a99151607c4952.id,
      key: _ctx.$citryPrepared.calls.citryCall00a99151607c4952.key
    }, {
      ['citrySlotfd0d5223a93ec546']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_cascader_option_17b40f7e, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld8516e7ab2570abe.id,
          key: _ctx.$citryPrepared.calls.citryCalld8516e7ab2570abe.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("button", { type: "submit" }, "Save category")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3755456437b74bdd2e3bd615a9308ebd90d2d275e7b099e57cdb49ae68eff675"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld8516e7ab2570abe","typeKey":"CCascaderOption_f18eaf","componentTag":"citry-c-cascader-option-17b40f7e","bindings":[]},{"localId":"citryCall00a99151607c4952","typeKey":"CCascader_d45a8e","componentTag":"citry-c-cascader-06b92651","bindings":[],"fills":[{"name":"citrySlotfd0d5223a93ec546","localDescendants":["citryCalld8516e7ab2570abe"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_cascader_forms_0097fa19 = _resolveComponent("citry-cascader-forms-0097fa19")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_cascader_forms_0097fa19, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0d5b309ff0a14161.id,
      key: _ctx.$citryPrepared.calls.citryCall0d5b309ff0a14161.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["82e83b841d3e703a6736f12833a2fc42994395304d654c7e9450aa4f628714ca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0d5b309ff0a14161","typeKey":"CascaderForms_2df3af","componentTag":"citry-cascader-forms-0097fa19","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
