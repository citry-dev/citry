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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  
  return (_openBlock(), _createElementBlock("section", { class: "switch-controlled" }, [
    (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
      checked: _ctx.enabled,
      onInput: $event => (_ctx.enabled = $event.target.checked),
      "citry-id": _ctx.$citryPrepared.calls.citryCallf1a5035c4e084361.id,
      key: _ctx.$citryPrepared.calls.citryCallf1a5035c4e084361.key
    }, {
      ['citrySlot25d46bc7bb328723']: _withCtx(() => [
        _createTextVNode("Reading mode")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["checked", "onInput", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.enabled ? 'Reading mode is on' : 'Reading mode is off')
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5389f10d717f2e3283b9c085d24c3b2405939cc6195fd2ff83c1c6f4cf3311cd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf1a5035c4e084361","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[{"kind":"prop","name":":checked","value":"enabled","sourceStart":64,"sourceEnd":82},{"kind":"event","name":"@input","value":"enabled = $event.target.checked","sourceStart":83,"sourceEnd":123}],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_switch_48689fdd = _resolveComponent("citry-controlled-switch-48689fdd")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_switch_48689fdd, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7e103ed87192af90.id,
      key: _ctx.$citryPrepared.calls.citryCall7e103ed87192af90.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e2df2fc2b5ae40172c0918060ac9c95e302c203908c0bafdd7dfad54357a24c8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7e103ed87192af90","typeKey":"ControlledSwitch_e0166d","componentTag":"citry-controlled-switch-48689fdd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
