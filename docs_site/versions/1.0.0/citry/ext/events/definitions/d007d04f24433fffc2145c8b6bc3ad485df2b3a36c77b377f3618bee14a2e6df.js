(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("picture", { "data-citry-ui-part": "picture" }, [
      _createElementVNode("source", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), null, 16 /* FULL_PROPS */),
      _createElementVNode("source", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), null, 16 /* FULL_PROPS */),
      _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["72f5b1ffdfcc3b99ff3e66b3aba3fe4dff48e7befeec450726eaf8134d8f6eab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-responsive" }, [
    _createElementVNode("p", null, " Resize across 48rem and 64rem. The browser selects the first matching source, then the final image candidates. "),
    _createElementVNode("div", { class: "image-responsive__pair" }, [
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "Template-fed records"),
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          onStatusChange: _ctx.showSelectedSource,
          "citry-id": _ctx.$citryPrepared.calls.citryCalle71d1fdb9b4dcb8c.id,
          key: _ctx.$citryPrepared.calls.citryCalle71d1fdb9b4dcb8c.key
        }, null, 8 /* PROPS */, ["onStatusChange", "citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "Python records"),
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall588bd3e419fe3984.id,
          key: _ctx.$citryPrepared.calls.citryCall588bd3e419fe3984.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ])
    ]),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Selected local fixture: ${_ctx.selected}`)
    }, " Selected local fixture: Waiting for native selection ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7a0b520b11914db343946ca9162984ce4675d93218ea353676a7af7310c25747"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle71d1fdb9b4dcb8c","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":onStatusChange","value":"showSelectedSource","sourceStart":287,"sourceEnd":323}]},{"localId":"citryCall588bd3e419fe3984","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_responsive_image_sources_a15d5e3d = _resolveComponent("citry-responsive-image-sources-a15d5e3d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_responsive_image_sources_a15d5e3d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6275d87edc01a1df.id,
      key: _ctx.$citryPrepared.calls.citryCall6275d87edc01a1df.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8f03bf7460fe65233ef3cc7fc34f27c4a0f014f12adeaf5c054f38c62fd4cfae"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6275d87edc01a1df","typeKey":"ResponsiveImageSources_344adf","componentTag":"citry-responsive-image-sources-a15d5e3d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
