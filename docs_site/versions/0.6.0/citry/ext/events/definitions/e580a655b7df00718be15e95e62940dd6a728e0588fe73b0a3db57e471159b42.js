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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a1c15ab13f28c61cc903c8a5f49027567a2d6874b9cfd0874c44555d02f6a869"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b3101334128cad0e2be47225ff3bd9cdd468129abbb5dacca88f350e9d694c01"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldbd35d57adfd13d7","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcf7f219585ceac80","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_customization_b5264a11 = _resolveComponent("citry-scroll-area-customization-b5264a11")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_customization_b5264a11, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1c06de519bb0529f.id,
      key: _ctx.$citryPrepared.calls.citryCall1c06de519bb0529f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["46cfcb39e150071e0c9aa1b2a95f1363dd8c546eaca74cf5fc4baac1467b960c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1c06de519bb0529f","typeKey":"ScrollAreaCustomization_ef37ee","componentTag":"citry-scroll-area-customization-b5264a11","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
