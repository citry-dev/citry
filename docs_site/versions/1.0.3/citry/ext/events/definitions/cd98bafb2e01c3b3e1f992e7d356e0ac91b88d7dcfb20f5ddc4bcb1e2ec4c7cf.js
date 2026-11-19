(function(Vue){
const { normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["efb69ca51f0584b45ba39a0c568b024f26b24463031aa0613b1369a8b34e40cc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withDirectives: _withDirectives, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_spinner_8904601b = _resolveComponent("citry-c-spinner-8904601b")
  
  return (_openBlock(), _createElementBlock("section", { class: "spinner-delayed" }, [
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (_ctx.visible = !_ctx.visible)
    }, "Toggle long-running observation", 8 /* PROPS */, ["onClick"]),
    _withDirectives(_createElementVNode("div", {
      key: "citryReplacementb18e4695f0d8c24294f74a8c451ed6738d721b490dc81d84ff70f2b0492d244b",
      class: "spinner-delayed__status"
    }, [
      (_openBlock(), _createBlock(_component_citry_c_spinner_8904601b, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall58747f40d88c8a17.id,
        key: _ctx.$citryPrepared.calls.citryCall58747f40d88c8a17.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("span", null, "Waiting for the long exposure")
    ], 512 /* NEED_PATCH */), [
      [_vShow, _ctx.visible]
    ]),
    _createElementVNode("p", null, "Real applications show this only after their chosen delay.")
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["26d468426099d733c341f3f77aa3be0a14ebf4ba66b1f34f5857e05d5ab34d18"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective6d7714cc30a722911460c99e00a3cc8d432605f59175f5ebd6c63ec4546883a0D0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective6d7714cc30a722911460c99e00a3cc8d432605f59175f5ebd6c63ec4546883a0","replacementKey":"citryReplacementb18e4695f0d8c24294f74a8c451ed6738d721b490dc81d84ff70f2b0492d244b","localDescendants":["citryCall58747f40d88c8a17"],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall58747f40d88c8a17","typeKey":"CSpinner_c40717","componentTag":"citry-c-spinner-8904601b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_delayed_spinner_71fe5770 = _resolveComponent("citry-delayed-spinner-71fe5770")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_delayed_spinner_71fe5770, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcd20e6357bf7ca0d.id,
      key: _ctx.$citryPrepared.calls.citryCallcd20e6357bf7ca0d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ba8d7c2eb779ff6a81fbfd1e92301b69f5049c8d1ffbf3319a8c71ce77f6ee21"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcd20e6357bf7ca0d","typeKey":"DelayedSpinner_5896b9","componentTag":"citry-delayed-spinner-71fe5770","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
