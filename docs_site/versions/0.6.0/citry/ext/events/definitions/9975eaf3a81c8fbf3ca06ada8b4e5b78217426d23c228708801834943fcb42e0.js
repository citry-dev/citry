(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9a4826fdbd426eba9635a88233d6dc82dc0ff0dafbd32a4471d49ff7954ef1bf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a92bfb37cf6448e3789d4f277ad4cbec8f3e958de6c986d9cf4faab17dffa973"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4de4e79e789883e9","typeKey":"CDateInput_135afc","componentTag":"citry-c-date-input-0233fc63","bindings":[]},{"localId":"citryCall5348642e9a26e4c8","typeKey":"CDateInput_135afc","componentTag":"citry-c-date-input-0233fc63","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_date_input_locales_199b2458 = _resolveComponent("citry-date-input-locales-199b2458")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_date_input_locales_199b2458, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6eff614a631fc9e4.id,
      key: _ctx.$citryPrepared.calls.citryCall6eff614a631fc9e4.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["741e277bfcc6b31dd3ac140cd8d0c1862e9905e8a4117a9d8d06d7e8a5395aff"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6eff614a631fc9e4","typeKey":"DateInputLocales_92e5f3","componentTag":"citry-date-input-locales-199b2458","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
