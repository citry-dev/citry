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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_avatar_59d27e85 = _resolveComponent("citry-c-avatar-59d27e85")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("div", { class: "avatar-reactive" }, [
    (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
      src: _ctx.source,
      onStatusChange: detail => _ctx.status = detail.status,
      "citry-id": _ctx.$citryPrepared.calls.citryCallfff28af3cff4bd7d.id,
      key: _ctx.$citryPrepared.calls.citryCallfff28af3cff4bd7d.key
    }, {
      ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
        _createTextVNode("ML")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["src", "onStatusChange", "citry-id"])),
    _createElementVNode("p", null, [
      _createTextVNode("Status: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.status)
      }, "fallback", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("div", { class: "avatar-reactive__actions" }, [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        onClick: $event => (_ctx.source = '/missing-lookout-a.png'),
        "citry-id": _ctx.$citryPrepared.calls.citryCalle6f5d6f948856d4c.id,
        key: _ctx.$citryPrepared.calls.citryCalle6f5d6f948856d4c.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Try missing image")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        onClick: $event => (_ctx.source = null),
        "citry-id": _ctx.$citryPrepared.calls.citryCallaace291d1f2814fa.id,
        key: _ctx.$citryPrepared.calls.citryCallaace291d1f2814fa.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Use fallback")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["634d949d3df6a0487e344d2bcb03c85971f57b00636cd913430923a0d8af58f8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfff28af3cff4bd7d","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[{"kind":"prop","name":":src","value":"source","sourceStart":58,"sourceEnd":71},{"kind":"prop","name":":onStatusChange","value":"detail => status = detail.status","sourceStart":72,"sourceEnd":122}],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle6f5d6f948856d4c","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"source = '/missing-lookout-a.png'","sourceStart":459,"sourceEnd":501}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallaace291d1f2814fa","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"source = null","sourceStart":753,"sourceEnd":775}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_reactive_b3697ec0 = _resolveComponent("citry-avatar-reactive-b3697ec0")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_reactive_b3697ec0, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9a670635de470e90.id,
      key: _ctx.$citryPrepared.calls.citryCall9a670635de470e90.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9d8b87e3e9e98a6989408377b26a3d5ace5773bb8f3d8c4fd75471e49269f9b9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9a670635de470e90","typeKey":"AvatarReactive_34159c","componentTag":"citry-avatar-reactive-b3697ec0","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
