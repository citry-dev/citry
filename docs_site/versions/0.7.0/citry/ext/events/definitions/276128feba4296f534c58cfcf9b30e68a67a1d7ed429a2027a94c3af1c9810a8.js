(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-scroll-area",
    tabindex: "0",
    "data-citry-ui-part": "scroll-area"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotdbd1d2942e04f334'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotdbd1d2942e04f334", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1515467170c655985883a90412c7d03f74d07fe291843c485cc0e24885499234"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-scroll-area",
    tabindex: "0",
    "data-citry-ui-part": "scroll-area"
  }, _ctx.$citryPrepared.citryAttrs0), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a4c5a714797ae737ee0f26c93c73758a11716a62e2aeb9599fbc7c6c551c7824"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-glance" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Recent activity"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall2a95d36c51f3d442.id,
        key: _ctx.$citryPrepared.calls.citryCall2a95d36c51f3d442.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("ol", { class: "scroll-area-glance__activity" }, [
            _createElementVNode("li", null, "Import completed"),
            _createElementVNode("li", null, "Review requested"),
            _createElementVNode("li", null, "Access approved"),
            _createElementVNode("li", null, "Build started"),
            _createElementVNode("li", null, "Checks completed"),
            _createElementVNode("li", null, "Release published"),
            _createElementVNode("li", null, "Audit archived")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Applied filters"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallb2d2610dbd488b3b.id,
        key: _ctx.$citryPrepared.calls.citryCallb2d2610dbd488b3b.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("div", { class: "scroll-area-glance__rail" }, [
            _createElementVNode("span", null, "Region: Central Europe"),
            _createElementVNode("span", null, "Status: Needs review"),
            _createElementVNode("span", null, "Owner: Operations"),
            _createElementVNode("span", null, "Window: Last 90 days")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Result matrix"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6f744ef91b04f225.id,
        key: _ctx.$citryPrepared.calls.citryCall6f744ef91b04f225.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("div", { class: "scroll-area-glance__matrix" }, [
            _createElementVNode("strong", null, "Service"),
            _createElementVNode("strong", null, "Owner"),
            _createElementVNode("strong", null, "Region"),
            _createElementVNode("span", null, "Accounts"),
            _createElementVNode("span", null, "Identity"),
            _createElementVNode("span", null, "Prague"),
            _createElementVNode("span", null, "Ledger"),
            _createElementVNode("span", null, "Finance"),
            _createElementVNode("span", null, "Berlin"),
            _createElementVNode("span", null, "Search"),
            _createElementVNode("span", null, "Discovery"),
            _createElementVNode("span", null, "Vienna"),
            _createElementVNode("span", null, "Archive"),
            _createElementVNode("span", null, "Records"),
            _createElementVNode("span", null, "Warsaw")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Python composition"),
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall825df21ec42d5b8d.id,
        key: _ctx.$citryPrepared.calls.citryCall825df21ec42d5b8d.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6e6205f6567553a96d6f96ae3c61e8c6a68a3055de86fb1386781b6cd3a47278"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2a95d36c51f3d442","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb2d2610dbd488b3b","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6f744ef91b04f225","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall825df21ec42d5b8d","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_at_a_glance_b28f0a8a = _resolveComponent("citry-scroll-area-at-a-glance-b28f0a8a")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_at_a_glance_b28f0a8a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1acf8995769d56a1.id,
      key: _ctx.$citryPrepared.calls.citryCall1acf8995769d56a1.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fe67f04d297b517e0695d1684d7da63a2e6a4fd0e52a6a3f83023cf574076824"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1acf8995769d56a1","typeKey":"ScrollAreaAtAGlance_8a9bc7","componentTag":"citry-scroll-area-at-a-glance-b28f0a8a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
