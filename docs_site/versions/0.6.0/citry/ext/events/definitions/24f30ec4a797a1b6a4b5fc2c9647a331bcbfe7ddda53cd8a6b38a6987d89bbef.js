(function(Vue){
const { withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, renderList: _renderList, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", { class: "demo-tabs" }, [
    _createElementVNode("div", {
      class: "demo-tabs__bar",
      role: "tablist",
      "aria-label": "Example sections"
    }, [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.tabs, (tab, index) => {
        return (_openBlock(), _createElementBlock("button", { ref_for: true, ref: (el) => _ctx.keepTabButton(index, el), id: _ctx.idPrefix + '-tab-' + index, type: "button", class: "demo-tabs__tab", role: "tab", "aria-controls": _ctx.idPrefix + '-panel-' + index, "aria-selected": index === _ctx.activeIndex, tabindex: index === _ctx.activeIndex ? 0 : -1, onClick: $event => (_ctx.activeIndex = index), onKeydown: $event => (_ctx.moveWithKeys($event, index)), textContent: _toDisplayString(tab.label) }, null, 40 /* PROPS, NEED_HYDRATION */, ["id", "aria-controls", "aria-selected", "tabindex", "onClick", "onKeydown", "textContent"]))
      }), 256 /* UNKEYED_FRAGMENT */))
    ]),
    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.tabs, (tab, index) => {
      return _withDirectives((_openBlock(), _createElementBlock("div", {
        key: "citryReplacementad2f2699db0ae496271d926b8fbad30635ffbf42808aa027a85d9fe04d3bff5f",
        id: _ctx.idPrefix + '-panel-' + index,
        class: "demo-tabs__panel",
        role: "tabpanel",
        tabindex: "0",
        "aria-labelledby": _ctx.idPrefix + '-tab-' + index,
        textContent: _toDisplayString(tab.body)
      }, null, 8 /* PROPS */, ["id", "aria-labelledby", "textContent"])), [
        [_vShow, index === _ctx.activeIndex]
      ])
    }), 256 /* UNKEYED_FRAGMENT */))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c22d4441cf8ea506e7f933c233e56a67277f60056591e8bc7728e145a821fd98"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective7eda3fda76b6563eeb23439a235cf4840b238a0cceddf64751ef47b7b1a93aeeD1","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective7eda3fda76b6563eeb23439a235cf4840b238a0cceddf64751ef47b7b1a93aee","replacementKey":"citryReplacementad2f2699db0ae496271d926b8fbad30635ffbf42808aa027a85d9fe04d3bff5f","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tabs_16529c82 = _resolveComponent("citry-tabs-16529c82")
  
  return (_openBlock(), _createBlock(_component_citry_tabs_16529c82, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallae882b9bf62924e3.id,
    key: _ctx.$citryPrepared.calls.citryCallae882b9bf62924e3.key
  }, null, 8 /* PROPS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c5a7b3a3ee77433a2f8b94bf632be61d1c1e8ba199f19fce78e14d9181f02cba"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallae882b9bf62924e3","typeKey":"Tabs_118635","componentTag":"citry-tabs-16529c82","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
