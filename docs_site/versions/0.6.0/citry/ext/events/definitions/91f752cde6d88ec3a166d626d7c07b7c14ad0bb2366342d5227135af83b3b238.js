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
      (_ctx.$citryPrepared.selectedSlots['citrySlot20df656fe6df3687'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot20df656fe6df3687", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["86483c86ad7fb6b00b213b70cbda3f82fdfbee3d7200b8b7d88fb0ed3125dfbc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      onStatusChange: (detail)=>{
        _ctx.callbacks++;
        _ctx.status=detail.status;
        _ctx.selected=_ctx.redact(detail.current_src || detail.src);
        if (detail.status === 'loaded') _ctx.nativeLoads++;
        if (detail.status === 'error') _ctx.nativeErrors++;
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCall8e09a1167b857247.id,
      key: _ctx.$citryPrepared.calls.citryCall8e09a1167b857247.key
    }, {
      ['citrySlot20df656fe6df3687']: _withCtx(() => [
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a250c85ceab7d938b9c79e1437345911a1d4c4c64b8943d5d7195c2b5b305142"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8e09a1167b857247","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":src","value":"source","sourceStart":544,"sourceEnd":557},{"kind":"prop","name":":onStatusChange","value":"(detail)=>{\n        callbacks++;\n        status=detail.status;\n        selected=redact(detail.current_src || detail.src);\n        if (detail.status === 'loaded') nativeLoads++;\n        if (detail.status === 'error') nativeErrors++;\n      }","sourceStart":558,"sourceEnd":815}],"fills":[{"name":"citrySlot20df656fe6df3687","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_reactive_image_d0bbe4f6 = _resolveComponent("citry-reactive-image-d0bbe4f6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_reactive_image_d0bbe4f6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2260e64d379e156b.id,
      key: _ctx.$citryPrepared.calls.citryCall2260e64d379e156b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["92a8eedb732c916234412983e9b280b2c2ea57f92489296bd3c4a73ae30c5184"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2260e64d379e156b","typeKey":"ReactiveImage_e60e1d","componentTag":"citry-reactive-image-d0bbe4f6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
