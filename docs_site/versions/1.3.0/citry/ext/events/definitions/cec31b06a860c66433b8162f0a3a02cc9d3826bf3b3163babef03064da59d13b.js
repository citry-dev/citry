(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-switch",
    "data-citry-ui-part": "switch"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-switch__input",
      type: "checkbox",
      role: "switch",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", { "data-citry-ui-part": "surface" }, [
      _createElementVNode("span", {
        "aria-hidden": "true",
        "data-citry-ui-part": "track"
      }, [
        _createElementVNode("span", { "data-citry-ui-part": "thumb" })
      ]),
      _createElementVNode("span", { "data-citry-ui-part": "body" }, [
        _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs2), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot25d46bc7bb328723'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot25d46bc7bb328723", { key: 0 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d1b11424a09888f95da567a1be0dd3a33b788b109b6caf20a55af8158e588d0a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  
  return (_openBlock(), _createElementBlock("section", { class: "switch-oak" }, [
    (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfb134ed3c37e867f.id,
      key: _ctx.$citryPrepared.calls.citryCallfb134ed3c37e867f.key
    }, {
      ['citrySlot25d46bc7bb328723']: _withCtx(() => [
        _createTextVNode("Oak reading nook")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d420a70b652318acb116512571e135cbfff14a44988655b3b21f718e4dec7d34"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfb134ed3c37e867f","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_custom_switch_fa7a9aaa = _resolveComponent("citry-custom-switch-fa7a9aaa")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_custom_switch_fa7a9aaa, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4b47bf8c4309d503.id,
      key: _ctx.$citryPrepared.calls.citryCall4b47bf8c4309d503.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b13467f7a0d462046cde33237f2a029cf431d2846805e009af4664e89d51a2ca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4b47bf8c4309d503","typeKey":"CustomSwitch_eacb8d","componentTag":"citry-custom-switch-fa7a9aaa","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
