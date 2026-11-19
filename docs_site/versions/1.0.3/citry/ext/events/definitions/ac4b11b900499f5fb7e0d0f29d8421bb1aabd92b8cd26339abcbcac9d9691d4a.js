(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      hidden: "",
      inert: "",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot3b118b957ecc918a'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot3b118b957ecc918a", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b9d6ccaea5b9cc19a71f209c7103f5b36d944e718f8d020d739dccff83424116"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-reactive" }, [
    _createElementVNode("div", { class: "image-reactive__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red')
      }, "Frame A", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/orion-nebula-1280.jpg?frame=fast-blue')
      }, "Frame B", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/missing-live-frame.jpg?frame=broken')
      }, "Broken", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.rapidAThenB())
      }, "Rapid A then B", 8 /* PROPS */, ["onClick"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
      src: _ctx.source,
      onStatusChange: _ctx.recordStatus,
      "citry-id": _ctx.$citryPrepared.calls.citryCallba6599763034cefa.id,
      key: _ctx.$citryPrepared.calls.citryCallba6599763034cefa.key
    }, {
      ['citrySlot3b118b957ecc918a']: _withCtx(() => [
        _createTextVNode("Survey frame unavailable")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["src", "onStatusChange", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(
      `Status ${_ctx.status}; selected ${_ctx.selected}; callbacks ${_ctx.callbacks};
      native load/error ${_ctx.nativeLoads}/${_ctx.nativeErrors}`
    )
    }, "Status waiting; selected none; callbacks 0; native load/error 0/0", 8 /* PROPS */, ["textContent"]),
    _createElementVNode("p", null, " The output redacts paths to filenames. onStatusChange reports the accepted native load or error settlement for the current image. "),
    _createElementVNode("div", {
      id: "image-reactive-shadow-host",
      "aria-label": "Open ShadowRoot fixture"
    })
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["17db9a86f5ba4e87e02357170ebb4e58b91d1deebd849c96414c1275b0ba572b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallba6599763034cefa","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":src","value":"source","sourceStart":544,"sourceEnd":557},{"kind":"prop","name":":onStatusChange","value":"recordStatus","sourceStart":558,"sourceEnd":588}],"fills":[{"name":"citrySlot3b118b957ecc918a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_reactive_image_ccf53204 = _resolveComponent("citry-reactive-image-ccf53204")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_reactive_image_ccf53204, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb6999830fd19e985.id,
      key: _ctx.$citryPrepared.calls.citryCallb6999830fd19e985.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["be84d90ccebf5c6840a3618bb16433e01b33d418b23fc346d16d2ceb97c6ec10"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb6999830fd19e985","typeKey":"ReactiveImage_a730ff","componentTag":"citry-reactive-image-ccf53204","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
