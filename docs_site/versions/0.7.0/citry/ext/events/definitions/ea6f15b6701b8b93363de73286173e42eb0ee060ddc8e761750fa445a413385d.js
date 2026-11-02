(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5030013a54e4512bc419cee6d4954405a6f4b48ab0f3458d11db465ca9fefbec"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_date_input_0233fc63 = _resolveComponent("citry-c-date-input-0233fc63")
  
  return (_openBlock(), _createElementBlock("section", { class: "date-input-demo-grid" }, [
    _createElementVNode("div", { lang: "en" }, [
      _createElementVNode("label", { for: "date-en" }, "English context"),
      (_openBlock(), _createBlock(_component_citry_c_date_input_0233fc63, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall4de4e79e789883e9.id,
        key: _ctx.$citryPrepared.calls.citryCall4de4e79e789883e9.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("div", {
      lang: "ar",
      dir: "rtl"
    }, [
      _createElementVNode("label", { for: "date-ar" }, "سياق عربي"),
      (_openBlock(), _createBlock(_component_citry_c_date_input_0233fc63, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall5348642e9a26e4c8.id,
        key: _ctx.$citryPrepared.calls.citryCall5348642e9a26e4c8.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("p", null, "The submitted value is 2026-08-19 in both controls; visible native formatting remains browser-owned.")
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d396df73391e75117c44503840035557105c23cf92d8c77af90d967570dba914"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4de4e79e789883e9","typeKey":"CDateInput_135afc","componentTag":"citry-c-date-input-0233fc63","bindings":[]},{"localId":"citryCall5348642e9a26e4c8","typeKey":"CDateInput_135afc","componentTag":"citry-c-date-input-0233fc63","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_date_input_locales_7fe7053c = _resolveComponent("citry-date-input-locales-7fe7053c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_date_input_locales_7fe7053c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5cd58990d384f544.id,
      key: _ctx.$citryPrepared.calls.citryCall5cd58990d384f544.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0007021e52ad950c8ae70deee14267157c3f1c24901a0ce466c7763aec2dacc0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5cd58990d384f544","typeKey":"DateInputLocales_314a99","componentTag":"citry-date-input-locales-7fe7053c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
