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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e9a1ae6e702434f319c409b104b3e19dd46d6d1d22048a12a9deb4830dad1ec6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective7eda3fda76b6563eeb23439a235cf4840b238a0cceddf64751ef47b7b1a93aeeD1","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective7eda3fda76b6563eeb23439a235cf4840b238a0cceddf64751ef47b7b1a93aee","replacementKey":"citryReplacementad2f2699db0ae496271d926b8fbad30635ffbf42808aa027a85d9fe04d3bff5f","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6391c432199fd62e72d21f37033dc65a6d29a8cf33173ff01d2822acbc476759"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallae882b9bf62924e3","typeKey":"Tabs_118635","componentTag":"citry-tabs-16529c82","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
