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
          (_ctx.$citryPrepared.selectedSlots['citrySlot68b9ec6d1edbf23f'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot68b9ec6d1edbf23f", { key: 0 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot748d23fb9d69de3c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot748d23fb9d69de3c", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cb14d33428d0661995e5895e27d19e832bed8714b1a1fe6a30c7846e2e4d931e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  
  return (_openBlock(), _createElementBlock("section", { class: "switch-room" }, [
    _createElementVNode("h2", null, "Evening room"),
    (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalledf2e1c249c90896.id,
      key: _ctx.$citryPrepared.calls.citryCalledf2e1c249c90896.key
    }, {
      ['citrySlot25d46bc7bb328723']: _withCtx(() => [
        _createTextVNode("Reading lamp")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla15ec25a824adde5.id,
      key: _ctx.$citryPrepared.calls.citryCalla15ec25a824adde5.key
    }, {
      ['citrySlot25d46bc7bb328723']: _withCtx(() => [
        _createTextVNode("Window shades")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb87351c732b2a8db.id,
      key: _ctx.$citryPrepared.calls.citryCallb87351c732b2a8db.key
    }, {
      ['citrySlot68b9ec6d1edbf23f']: _withCtx(() => [
        _createTextVNode("Quiet ventilation")
      ]),
      ['citrySlot748d23fb9d69de3c']: _withCtx(() => [
        _createTextVNode("Keep air moving below the bedroom.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5cd452163477ba93582ebd61c8441d48a3fc879a9b1f8b08de4f1e8d6b138283"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalledf2e1c249c90896","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla15ec25a824adde5","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb87351c732b2a8db","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot68b9ec6d1edbf23f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot748d23fb9d69de3c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_switch_at_a_glance_63b8240b = _resolveComponent("citry-switch-at-a-glance-63b8240b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_switch_at_a_glance_63b8240b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb31839a1d334e7c2.id,
      key: _ctx.$citryPrepared.calls.citryCallb31839a1d334e7c2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["73bafa695c1016719e14f5048019087450903212de336daaf526ab1e3b7ab7f9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb31839a1d334e7c2","typeKey":"SwitchAtAGlance_80a9da","componentTag":"citry-switch-at-a-glance-63b8240b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
