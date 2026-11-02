(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-number-input",
    "data-citry-ui-part": "number-input"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      _createElementVNode("button", _mergeProps({
        type: "button",
        tabindex: "-1",
        "data-citry-ui-part": "decrement"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("span", { "aria-hidden": "true" }, "−")
      ], 16 /* FULL_PROPS */),
      _withDirectives(_createElementVNode("input", _mergeProps({
        type: "text",
        role: "spinbutton",
        inputmode: "decimal",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ]),
      _createElementVNode("button", _mergeProps({
        type: "button",
        tabindex: "-1",
        "data-citry-ui-part": "increment"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", { "aria-hidden": "true" }, "+")
      ], 16 /* FULL_PROPS */)
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      disabled: ""
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["aebd83fc1095a940f641070270f466daca470d7f64b9c5c7ed5c6417153ab454"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_number_input_bb49fdfe = _resolveComponent("citry-c-number-input-bb49fdfe")
  
  return (_openBlock(), _createElementBlock("section", { class: "number-input-example-stack" }, [
    _createElementVNode("p", null, [
      _createTextVNode(" Place the same component under a client-enabled "),
      _createElementVNode("code", null, "<c-i18n>"),
      _createTextVNode(" provider to switch locale in place. ")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_number_input_bb49fdfe, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4205a7ea78ceba64.id,
      key: _ctx.$citryPrepared.calls.citryCall4205a7ea78ceba64.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    _createElementVNode("p", null, [
      _createTextVNode(" The editor and its ARIA value text use the provider locale; the enhanced Form value stays "),
      _createElementVNode("code", null, "1234.5"),
      _createTextVNode(". ")
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["471eab2c627269dbbd6e2fbd512f0b8f7e5ea2229125896c7314458ea5fbf086"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4205a7ea78ceba64","typeKey":"CNumberInput_3f8aee","componentTag":"citry-c-number-input-bb49fdfe","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_localized_number_input_6309a10d = _resolveComponent("citry-localized-number-input-6309a10d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_localized_number_input_6309a10d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall039ad6dfc2dbe875.id,
      key: _ctx.$citryPrepared.calls.citryCall039ad6dfc2dbe875.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2e0aca37acbc4c2c1d6cf79e79959918ac613e6be338251dcabbadf05045a392"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall039ad6dfc2dbe875","typeKey":"LocalizedNumberInput_fdcdf8","componentTag":"citry-localized-number-input-6309a10d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
