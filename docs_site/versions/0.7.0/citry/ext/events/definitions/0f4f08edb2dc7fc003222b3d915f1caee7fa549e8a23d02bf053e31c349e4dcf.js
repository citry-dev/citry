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
        (_ctx.$citryPrepared.selectedSlots['citrySlotee4ced8dcf18698d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotee4ced8dcf18698d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6e1554d25e44badc3c578ef388c32df94d1f66423af39ac3de671a8fb7dbefdf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_checkbox_eb6eae85 = _resolveComponent("citry-c-checkbox-eb6eae85")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "botanical-checklist",
    "aria-label": "Botanical field checklist"
  }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Morning survey"),
      _createElementVNode("h2", null, "Woodland observations")
    ]),
    _createElementVNode("div", { class: "botanical-checklist__grid" }, [
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall474a0e6db9d5de3f.id,
        key: _ctx.$citryPrepared.calls.citryCall474a0e6db9d5de3f.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Lady fern unfurled ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall96097b31ed82265b.id,
        key: _ctx.$citryPrepared.calls.citryCall96097b31ed82265b.key
      }, {
        ['citrySlot46b79f3889e5731e']: _withCtx(() => [
          _createTextVNode("Cushion moss fruiting")
        ]),
        ['citrySlot77e9b36d74732681']: _withCtx(() => [
          _createTextVNode(" Check the shaded side of fallen trunks. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall2cebcdf9b6ec2b3e.id,
        key: _ctx.$citryPrepared.calls.citryCall2cebcdf9b6ec2b3e.key
      }, {
        ['citrySlotee4ced8dcf18698d']: _withCtx(() => [
          _createTextVNode(" Reindeer lichen present ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_checkbox_eb6eae85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall9b078c594af51cf9.id,
        key: _ctx.$citryPrepared.calls.citryCall9b078c594af51cf9.key
      }, {
        ['citrySlot46b79f3889e5731e']: _withCtx(() => [
          _createTextVNode("Alpine saxifrage")
        ]),
        ['citrySlot77e9b36d74732681']: _withCtx(() => [
          _createTextVNode(" Outside this survey's elevation range. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["90529d402f4f1939c8dc95d6f70ca1cd19b48c83f9e5081a5b533e5368dd992d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall474a0e6db9d5de3f","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall96097b31ed82265b","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2cebcdf9b6ec2b3e","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlotee4ced8dcf18698d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9b078c594af51cf9","typeKey":"CCheckbox_05d638","componentTag":"citry-c-checkbox-eb6eae85","bindings":[],"fills":[{"name":"citrySlot46b79f3889e5731e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot77e9b36d74732681","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_checkbox_at_a_glance_51b4b6e6 = _resolveComponent("citry-checkbox-at-a-glance-51b4b6e6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_checkbox_at_a_glance_51b4b6e6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2d11d13064541b0e.id,
      key: _ctx.$citryPrepared.calls.citryCall2d11d13064541b0e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ac441c24742e940d1e61b43e821eff3a92d3b04ca84fe93cee7cb13080fc2003"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2d11d13064541b0e","typeKey":"CheckboxAtAGlance_3c75bc","componentTag":"citry-checkbox-at-a-glance-51b4b6e6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
