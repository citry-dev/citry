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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_avatar_59d27e85 = _resolveComponent("citry-c-avatar-59d27e85")
  
  return (_openBlock(), _createElementBlock("div", { class: "avatar-name-list" }, [
    _createElementVNode("div", null, [
      (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall34960af2a26973bc.id,
        key: _ctx.$citryPrepared.calls.citryCall34960af2a26973bc.key
      }, {
        ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
          _createTextVNode("MV")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("span", null, "Named identity")
    ]),
    _createElementVNode("div", null, [
      (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6a4cc9994a29c4e6.id,
        key: _ctx.$citryPrepared.calls.citryCall6a4cc9994a29c4e6.key
      }, {
        ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
          _createElementVNode("span", { "aria-hidden": "true" }, "MF")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("span", null, "Decorative companion")
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f50a6544b41dc0594087f7b3b899637f0f0d55de6fc205f44cb87a6915c33e1c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall34960af2a26973bc","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6a4cc9994a29c4e6","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_names_0ea8e430 = _resolveComponent("citry-avatar-names-0ea8e430")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_names_0ea8e430, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalleeb3caf43a387a61.id,
      key: _ctx.$citryPrepared.calls.citryCalleeb3caf43a387a61.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d1974745172311a1a4299c2c7ee27f11999c7f1d392440fb0ee65dfac68a090d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalleeb3caf43a387a61","typeKey":"AvatarNames_dcdbef","componentTag":"citry-avatar-names-0ea8e430","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
