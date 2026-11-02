(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    tabindex: "0",
    "data-citry-ui-part": "scroll-area"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotdbd1d2942e04f334'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotdbd1d2942e04f334", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["39236e0c33a54de25424e27fa1d70bbe8c1eca9965f1dd83fa3d52f3da728124"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-customization" }, [
    _createElementVNode("article", { class: "scroll-area-brand scroll-area-brand--orchard" }, [
      _createElementVNode("h3", null, "Orchard notes"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalldbd35d57adfd13d7.id,
        key: _ctx.$citryPrepared.calls.citryCalldbd35d57adfd13d7.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("div", { class: "scroll-area-customization__notes" }, [
            _createElementVNode("p", null, "Pear block: pollinator rows checked."),
            _createElementVNode("p", null, "North field: irrigation pressure normal."),
            _createElementVNode("p", null, "West field: pruning review scheduled."),
            _createElementVNode("p", null, "Harvest window: seven days remaining."),
            _createElementVNode("p", null, "Cold store: capacity confirmed.")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", {
      class: "scroll-area-brand scroll-area-brand--harbor",
      style: "color-scheme:dark"
    }, [
      _createElementVNode("h3", null, "Harbor notes"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallcf7f219585ceac80.id,
        key: _ctx.$citryPrepared.calls.citryCallcf7f219585ceac80.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("div", { class: "scroll-area-customization__notes" }, [
            _createElementVNode("p", null, "North berth: loading complete."),
            _createElementVNode("p", null, "East pier: tide window confirmed."),
            _createElementVNode("p", null, "Customs desk: manifest approved."),
            _createElementVNode("p", null, "Harbor pilot: departure booked."),
            _createElementVNode("p", null, "Weather station: visibility clear.")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7c5ce4b97baa139e36581815510b38f891a257681b2d33b8aa462b07fe7249f6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldbd35d57adfd13d7","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcf7f219585ceac80","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_customization_008ba378 = _resolveComponent("citry-scroll-area-customization-008ba378")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_customization_008ba378, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall722ada48a37457f7.id,
      key: _ctx.$citryPrepared.calls.citryCall722ada48a37457f7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["26ecc8aca63373cc0f78a5b46d943649766b14789f58cb7eec8387e16887ea54"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall722ada48a37457f7","typeKey":"ScrollAreaCustomization_724e75","componentTag":"citry-scroll-area-customization-008ba378","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
