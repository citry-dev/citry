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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["d0951307a90f753b76f32c07e6e23042937dbfdd7ecec4827b7609922bae99c1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9ca051703088ea004cfb4cd2b44d239fd81e3425724c8f854efe66ee5a864077"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf1a5035c4e084361","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[{"kind":"prop","name":":checked","value":"enabled","sourceStart":64,"sourceEnd":82},{"kind":"event","name":"@input","value":"enabled = $event.target.checked","sourceStart":83,"sourceEnd":123}],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_switch_b584addb = _resolveComponent("citry-controlled-switch-b584addb")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_switch_b584addb, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfa0a84e4ede82c57.id,
      key: _ctx.$citryPrepared.calls.citryCallfa0a84e4ede82c57.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["11b20ffdfb763ec2986f883212de48095324b6ae6e0af01f8fc945ff6cf109b4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfa0a84e4ede82c57","typeKey":"ControlledSwitch_6eebd1","componentTag":"citry-controlled-switch-b584addb","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
