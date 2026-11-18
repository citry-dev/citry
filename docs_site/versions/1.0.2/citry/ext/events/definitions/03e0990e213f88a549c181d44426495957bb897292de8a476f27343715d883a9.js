(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-radio",
    "data-citry-ui-part": "radio"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-radio__input",
      type: "radio",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", { "data-citry-ui-part": "body" }, [
      _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlotee162e134278aeb7'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotee162e134278aeb7", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["15cdd5e8f8590ecb8d4a6b4f9ac84a8675382d8532f3e4d4ca4e2e4c22e996cf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("fieldset", _mergeProps({
    class: "cui-radio-group",
    "data-citry-ui-part": "radio-group"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("legend", { "data-citry-ui-part": "legend" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot5c7144b1ccbd8c0a'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot5c7144b1ccbd8c0a", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    (_ctx.$citryPrepared.selectedSlots['citrySlot4a98261f99d55a9d'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot4a98261f99d55a9d", { key: 1 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ec9d448e78a87946c7fcadc1d3b972a522792e39d610f1df7f4a17a92c3abb3c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_radio_81d18614 = _resolveComponent("citry-c-radio-81d18614")
  const _component_citry_c_radio_group_1a2c5c3f = _resolveComponent("citry-c-radio-group-1a2c5c3f")
  
  return (_openBlock(), _createElementBlock("section", { class: "radio-glance" }, [
    _createElementVNode("h2", null, "Plan the garden path"),
    _createElementVNode("p", null, "Choose the habitat the path should pass through."),
    (_openBlock(), _createBlock(_component_citry_c_radio_group_1a2c5c3f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5def2e63013dbaca.id,
      key: _ctx.$citryPrepared.calls.citryCall5def2e63013dbaca.key
    }, {
      ['citrySlot5c7144b1ccbd8c0a']: _withCtx(() => [
        _createTextVNode("Habitat")
      ]),
      ['citrySlot4a98261f99d55a9d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_radio_81d18614, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall94d9efabb81f8dc2.id,
          key: _ctx.$citryPrepared.calls.citryCall94d9efabb81f8dc2.key
        }, {
          ['citrySlotee162e134278aeb7']: _withCtx(() => [
            _createTextVNode("Woodland")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_radio_81d18614, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall454dfd5ed8b43715.id,
          key: _ctx.$citryPrepared.calls.citryCall454dfd5ed8b43715.key
        }, {
          ['citrySlotee162e134278aeb7']: _withCtx(() => [
            _createTextVNode("Wildflower meadow")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_radio_81d18614, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallb75a576ad8a041ef.id,
          key: _ctx.$citryPrepared.calls.citryCallb75a576ad8a041ef.key
        }, {
          ['citrySlotee162e134278aeb7']: _withCtx(() => [
            _createTextVNode("Wetland edge")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ff7e28d215266b2d6224e9caffacd09d42f0cae8b10a04ad1b553f83a728ecfd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall94d9efabb81f8dc2","typeKey":"CRadio_483d27","componentTag":"citry-c-radio-81d18614","bindings":[],"fills":[{"name":"citrySlotee162e134278aeb7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall454dfd5ed8b43715","typeKey":"CRadio_483d27","componentTag":"citry-c-radio-81d18614","bindings":[],"fills":[{"name":"citrySlotee162e134278aeb7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb75a576ad8a041ef","typeKey":"CRadio_483d27","componentTag":"citry-c-radio-81d18614","bindings":[],"fills":[{"name":"citrySlotee162e134278aeb7","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5def2e63013dbaca","typeKey":"CRadioGroup_38ad5d","componentTag":"citry-c-radio-group-1a2c5c3f","bindings":[],"fills":[{"name":"citrySlot4a98261f99d55a9d","localDescendants":["citryCall454dfd5ed8b43715","citryCall94d9efabb81f8dc2","citryCallb75a576ad8a041ef"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5c7144b1ccbd8c0a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_radio_at_a_glance_bffc8dcc = _resolveComponent("citry-radio-at-a-glance-bffc8dcc")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_radio_at_a_glance_bffc8dcc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9fae71f6576413bd.id,
      key: _ctx.$citryPrepared.calls.citryCall9fae71f6576413bd.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3d46f539150dfcc0d2bb6bb4ab328fe2b2cb823a2a6ae581b33ebfc081e139c2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9fae71f6576413bd","typeKey":"RadioAtAGlance_3ea408","componentTag":"citry-radio-at-a-glance-bffc8dcc","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
