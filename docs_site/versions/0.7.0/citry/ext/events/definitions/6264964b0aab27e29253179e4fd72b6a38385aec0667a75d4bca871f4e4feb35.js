(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-badge",
    "data-citry-ui-part": "badge"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-badge__label",
      "data-citry-ui-part": "label"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot342d600796e3f7d6'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot342d600796e3f7d6", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0f33d496b71a20b9ad95bf939b3cf49a23e416edc91f625c2c4128e5bd6ac1ac"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-3bed3ea0af7a1780", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotb13ff7dbfcd5f34a'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotb13ff7dbfcd5f34a", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0adfeb1903c9250150e0a3d058316d216477a18bf78a56c396d8635da8b31dce"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_badge_20fd07c8 = _resolveComponent("citry-c-badge-20fd07c8")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallb970eacf61d5afbf.id,
    key: _ctx.$citryPrepared.calls.citryCallb970eacf61d5afbf.key
  }, {
    ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
      _createElementVNode("div", { class: "badge-themes__quartz" }, [
        (_openBlock(), _createBlock(_component_citry_c_badge_20fd07c8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallf7256c3dd0a2ce8b.id,
          key: _ctx.$citryPrepared.calls.citryCallf7256c3dd0a2ce8b.key
        }, {
          ['citrySlot342d600796e3f7d6']: _withCtx(() => [
            _createTextVNode("Quartz archive")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _createElementVNode("div", { class: "badge-themes__basalt" }, [
        (_openBlock(), _createBlock(_component_citry_c_badge_20fd07c8, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld26a2dd0db4d81bf.id,
          key: _ctx.$citryPrepared.calls.citryCalld26a2dd0db4d81bf.key
        }, {
          ['citrySlot342d600796e3f7d6']: _withCtx(() => [
            _createTextVNode("Basalt archive")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3f746331ec66057d7524847ee3cfda01996a09bad83e965fe7835f71a8f65c92"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf7256c3dd0a2ce8b","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld26a2dd0db4d81bf","typeKey":"CBadge_20b1a5","componentTag":"citry-c-badge-20fd07c8","bindings":[],"fills":[{"name":"citrySlot342d600796e3f7d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb970eacf61d5afbf","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":["citryCalld26a2dd0db4d81bf","citryCallf7256c3dd0a2ce8b"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_badge_customization_b24acb48 = _resolveComponent("citry-badge-customization-b24acb48")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_badge_customization_b24acb48, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7fb497c88f98c7a3.id,
      key: _ctx.$citryPrepared.calls.citryCall7fb497c88f98c7a3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["96de7cc09b32f67c1999fc96956986d10e781d8fd73d99979828451d2d0918ba"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7fb497c88f98c7a3","typeKey":"BadgeCustomization_f68eb3","componentTag":"citry-badge-customization-b24acb48","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
