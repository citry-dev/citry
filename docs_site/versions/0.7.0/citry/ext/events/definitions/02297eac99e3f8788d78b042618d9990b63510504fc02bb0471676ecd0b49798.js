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
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-4db931dd4fd5ad47", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot0d2ecfee87db4621'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot0d2ecfee87db4621", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["182ced09199ba5a266177a942bdbb3353b37ffbb805fe4ca6238a3f0cb46353f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-4db931dd4fd5ad47","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-4db931dd4fd5ad47","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  const _component_citry_c_col_37f35bc5 = _resolveComponent("citry-c-col-37f35bc5")
  
  return (_openBlock(), _createBlock(_component_citry_c_col_37f35bc5, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallc07ef9cfa958e9af.id,
    key: _ctx.$citryPrepared.calls.citryCallc07ef9cfa958e9af.key
  }, {
    ['citrySlot0d2ecfee87db4621']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalld37eeade1a395aa7.id,
        key: _ctx.$citryPrepared.calls.citryCalld37eeade1a395aa7.key
      }, {
        ['citrySlot25d46bc7bb328723']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0) + " switch", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall898234242bba8c38.id,
        key: _ctx.$citryPrepared.calls.citryCall898234242bba8c38.key
      }, {
        ['citrySlot25d46bc7bb328723']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1) + " switch", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallea66ca879506af29.id,
        key: _ctx.$citryPrepared.calls.citryCallea66ca879506af29.key
      }, {
        ['citrySlot25d46bc7bb328723']: _withCtx(() => [
          _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2) + " switch", 1 /* TEXT */)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallacb011e065650dee.id,
        key: _ctx.$citryPrepared.calls.citryCallacb011e065650dee.key
      }, {
        ['citrySlot25d46bc7bb328723']: _withCtx(() => [
          _createTextVNode("Label before track")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bea6b67f7479ba1766ba550aa7b13feed789109b4751994d845bf4ef8876c3f0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld37eeade1a395aa7","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall898234242bba8c38","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallea66ca879506af29","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallacb011e065650dee","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot25d46bc7bb328723","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc07ef9cfa958e9af","typeKey":"CCol_a23ecf","componentTag":"citry-c-col-37f35bc5","bindings":[],"fills":[{"name":"citrySlot0d2ecfee87db4621","localDescendants":["citryCall898234242bba8c38","citryCallacb011e065650dee","citryCalld37eeade1a395aa7","citryCallea66ca879506af29"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_switch_presentation_1b591aca = _resolveComponent("citry-switch-presentation-1b591aca")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_switch_presentation_1b591aca, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallda5fcf45946fcfb1.id,
      key: _ctx.$citryPrepared.calls.citryCallda5fcf45946fcfb1.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4a9c09c53d6da5fec29ac0d367fc3b2bc91530058f8811907bd850dfc903adab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallda5fcf45946fcfb1","typeKey":"SwitchPresentation_0abe86","componentTag":"citry-switch-presentation-1b591aca","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
