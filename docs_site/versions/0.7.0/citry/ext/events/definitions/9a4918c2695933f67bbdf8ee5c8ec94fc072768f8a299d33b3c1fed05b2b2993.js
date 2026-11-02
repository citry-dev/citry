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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b4fa3a1da54482c36a9d18ca6a6bfd1c80c7c2c1ba534524c41e8c045c8c8abd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-checkbox",
    "data-citry-ui-part": "checkbox"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-checkbox__input",
      type: "checkbox",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", { class: "cui-checkbox__body" }, [
      _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot46b79f3889e5731e'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot46b79f3889e5731e", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot77e9b36d74732681'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot77e9b36d74732681", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d37012a65a9c7e4d1e73a5117d2a3ad47d3a01ab5fe920180b47d12400e07e48"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  const _component_citry_c_checkbox_eb6eae85 = _resolveComponent("citry-c-checkbox-eb6eae85")
  const _component_citry_c_col_37f35bc5 = _resolveComponent("citry-c-col-37f35bc5")
  
  return (_openBlock(), _createBlock(_component_citry_c_col_37f35bc5, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall701159af88a83a1b.id,
    key: _ctx.$citryPrepared.calls.citryCall701159af88a83a1b.key
  }, {
    ['citrySlot0d2ecfee87db4621']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalla57da9ae616b3dbf.id,
        key: _ctx.$citryPrepared.calls.citryCalla57da9ae616b3dbf.key
      }, {
        ['citrySlot68b9ec6d1edbf23f']: _withCtx(() => [
          _createTextVNode("Automatic hallway lighting")
        ]),
        ['citrySlot748d23fb9d69de3c']: _withCtx(() => [
          _createTextVNode("Takes effect immediately.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalla0f4f91774957f71.id,
        key: _ctx.$citryPrepared.calls.citryCalla0f4f91774957f71.key
      }, {
        ['citrySlot46b79f3889e5731e']: _withCtx(() => [
          _createTextVNode("Include spare keys in the move checklist")
        ]),
        ['citrySlot77e9b36d74732681']: _withCtx(() => [
          _createTextVNode("A selection, not an immediate setting.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["34af43443b984967fb0639085d2189f1ead6a5f31603d14533304b7b4030745a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla57da9ae616b3dbf","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot68b9ec6d1edbf23f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot748d23fb9d69de3c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla0f4f91774957f71","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall701159af88a83a1b","typeKey":"CCol_a23ecf","componentTag":"citry-c-col-37f35bc5","bindings":[],"fills":[{"name":"citrySlot0d2ecfee87db4621","localDescendants":["citryCalla0f4f91774957f71","citryCalla57da9ae616b3dbf"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_choice_semantics_a98f7569 = _resolveComponent("citry-choice-semantics-a98f7569")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_choice_semantics_a98f7569, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall23801a850a64c742.id,
      key: _ctx.$citryPrepared.calls.citryCall23801a850a64c742.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["34c2a67b02c4a7fc20c1f7322de49f650525ceaf3640ec5dc6dc8d57e25f20b8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall23801a850a64c742","typeKey":"ChoiceSemantics_ab2292","componentTag":"citry-choice-semantics-a98f7569","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
