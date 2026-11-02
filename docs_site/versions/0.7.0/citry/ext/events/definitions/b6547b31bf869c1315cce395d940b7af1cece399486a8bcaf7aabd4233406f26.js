(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-avatar",
    "data-citry-ui-part": "avatar"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-avatar__fallback",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7cf7eb35c5daa87'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7cf7eb35c5daa87", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b96277b515ed108195a76b351c5a2eed4418ed0a5d7773c33d7a9a5a00908156"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-hover-card-host",
    "data-citry-hover-card-host": "",
    "data-citry-ui-part": "host"
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot5acfa23a00dd4e44'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot5acfa23a00dd4e44", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-hover-card",
      popover: "manual",
      "aria-hidden": "true",
      "data-citry-ui-part": "hover-card"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", { "data-citry-ui-part": "content" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot3f4ff818ad71f2c3'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot3f4ff818ad71f2c3", { key: 1 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("span", {
        "aria-hidden": "true",
        "data-citry-ui-part": "arrow"
      })
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["afcbb64cd3e879dce639ead8238a1058fed0e999b8c67c1b97121a90061dc209"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_avatar_59d27e85 = _resolveComponent("citry-c-avatar-59d27e85")
  const _component_citry_c_col_37f35bc5 = _resolveComponent("citry-c-col-37f35bc5")
  const _component_citry_c_hover_card_44054f9b = _resolveComponent("citry-c-hover-card-44054f9b")
  
  return (_openBlock(), _createElementBlock("p", null, [
    _createTextVNode("Meet "),
    (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla4d2097180404a9e.id,
      key: _ctx.$citryPrepared.calls.citryCalla4d2097180404a9e.key
    }, {
      ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
        _createElementVNode("a", _mergeProps({ href: "#maya" }, _ctx.$citryPrepared.citryAttrs0), "Maya Chen", 16 /* FULL_PROPS */)
      ]),
      ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_col_37f35bc5, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall31320be731cbe343.id,
          key: _ctx.$citryPrepared.calls.citryCall31320be731cbe343.key
        }, {
          ['citrySlot0d2ecfee87db4621']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalle4a739a1abfb6351.id,
              key: _ctx.$citryPrepared.calls.citryCalle4a739a1abfb6351.key
            }, {
              ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
                _createTextVNode("MC")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            _createElementVNode("strong", null, "Maya Chen"),
            _createElementVNode("span", null, "Field researcher · 18 shared observations")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a7d6d651c2731424d18f32effa6d8065f80740b018fc67d3ec47619fd8d0e7bd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle4a739a1abfb6351","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall31320be731cbe343","typeKey":"CCol_a23ecf","componentTag":"citry-c-col-37f35bc5","bindings":[],"fills":[{"name":"citrySlot0d2ecfee87db4621","localDescendants":["citryCalle4a739a1abfb6351"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla4d2097180404a9e","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":["citryCall31320be731cbe343","citryCalle4a739a1abfb6351"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_hover_card_at_a_glance_08a85918 = _resolveComponent("citry-hover-card-at-a-glance-08a85918")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_hover_card_at_a_glance_08a85918, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall635745dcc9ab71e5.id,
      key: _ctx.$citryPrepared.calls.citryCall635745dcc9ab71e5.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a7216f69f683106707f160d56c38c7e89b88a609b03b64c8c48a938b0876d387"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall635745dcc9ab71e5","typeKey":"HoverCardAtAGlance_363343","componentTag":"citry-hover-card-at-a-glance-08a85918","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
