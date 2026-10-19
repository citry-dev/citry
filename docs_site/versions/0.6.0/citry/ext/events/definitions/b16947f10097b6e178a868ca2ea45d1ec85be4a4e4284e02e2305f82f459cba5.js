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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4e0a4a8620f25db3340e3fa999dcc97fd717899f6026662f313724ebcfe8d750"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-wide-table" }, [
    _createElementVNode("h2", { id: "quarterly-results-title" }, "Quarterly service results"),
    _createElementVNode("p", null, " The Table keeps its caption and headers. ScrollArea only bounds the two-dimensional viewport. "),
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (_ctx.direction=_ctx.direction === 'ltr' ? 'rtl' : 'ltr')
    }, "Flip table direction", 8 /* PROPS */, ["onClick"]),
    _createElementVNode("div", { dir: _ctx.direction }, [
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall099b9e03ff088732.id,
        key: _ctx.$citryPrepared.calls.citryCall099b9e03ff088732.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("table", { class: "scroll-area-wide-table__table" }, [
            _createElementVNode("caption", null, "Latency and availability by quarter"),
            _createElementVNode("thead", null, [
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "col" }, "Service"),
                _createElementVNode("th", { scope: "col" }, "Q1 latency"),
                _createElementVNode("th", { scope: "col" }, "Q2 latency"),
                _createElementVNode("th", { scope: "col" }, "Q3 latency"),
                _createElementVNode("th", { scope: "col" }, "Q4 latency"),
                _createElementVNode("th", { scope: "col" }, "Availability")
              ])
            ]),
            _createElementVNode("tbody", null, [
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "row" }, [
                  _createElementVNode("a", { href: "#quarterly-results-title" }, "Accounts")
                ]),
                _createElementVNode("td", null, "112 ms"),
                _createElementVNode("td", null, "104 ms"),
                _createElementVNode("td", null, "98 ms"),
                _createElementVNode("td", null, "91 ms"),
                _createElementVNode("td", null, "99.99%")
              ]),
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "row" }, [
                  _createElementVNode("a", { href: "#quarterly-results-title" }, "Ledger")
                ]),
                _createElementVNode("td", null, "190 ms"),
                _createElementVNode("td", null, "172 ms"),
                _createElementVNode("td", null, "160 ms"),
                _createElementVNode("td", null, "151 ms"),
                _createElementVNode("td", null, "99.97%")
              ]),
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "row" }, [
                  _createElementVNode("a", { href: "#quarterly-results-title" }, "Search")
                ]),
                _createElementVNode("td", null, "86 ms"),
                _createElementVNode("td", null, "81 ms"),
                _createElementVNode("td", null, "74 ms"),
                _createElementVNode("td", null, "69 ms"),
                _createElementVNode("td", null, "99.95%")
              ]),
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "row" }, [
                  _createElementVNode("a", { href: "#quarterly-results-title" }, "Archive")
                ]),
                _createElementVNode("td", null, "244 ms"),
                _createElementVNode("td", null, "231 ms"),
                _createElementVNode("td", null, "218 ms"),
                _createElementVNode("td", null, "205 ms"),
                _createElementVNode("td", null, "99.90%")
              ]),
              _createElementVNode("tr", null, [
                _createElementVNode("th", { scope: "row" }, [
                  _createElementVNode("a", { href: "#quarterly-results-title" }, "Reports")
                ]),
                _createElementVNode("td", null, "155 ms"),
                _createElementVNode("td", null, "149 ms"),
                _createElementVNode("td", null, "141 ms"),
                _createElementVNode("td", null, "134 ms"),
                _createElementVNode("td", null, "99.96%")
              ])
            ])
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ], 8 /* PROPS */, ["dir"]),
    _createElementVNode("p", { class: "scroll-area-wide-table__print-note" }, " This fixture supplies its own compact print table so the final column fits inside the physical page. ")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["91d8f70510c87aaa65cfafd858f7faaaf61b78eabba764f37ab30d0c13a70c4a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall099b9e03ff088732","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_wide_table_91e67624 = _resolveComponent("citry-scroll-area-wide-table-91e67624")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_wide_table_91e67624, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7f438b24f0425693.id,
      key: _ctx.$citryPrepared.calls.citryCall7f438b24f0425693.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ab3bc35981a6530d12ca456831b6f7a68c57e3165c98b95ce2625f7414136915"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7f438b24f0425693","typeKey":"ScrollAreaWideTable_b5820f","componentTag":"citry-scroll-area-wide-table-91e67624","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
