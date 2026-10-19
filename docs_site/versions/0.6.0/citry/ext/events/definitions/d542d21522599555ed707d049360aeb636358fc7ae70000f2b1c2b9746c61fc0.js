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
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-nested" }, [
    _createElementVNode("h2", null, "Operations document"),
    _createElementVNode("p", null, " The outer document and inner inspector are separate native scroll containers. Tab order and gesture targeting stay with the browser. "),
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (_ctx.direction=_ctx.direction === 'ltr' ? 'rtl' : 'ltr')
    }, "Flip document direction", 8 /* PROPS */, ["onClick"]),
    _createElementVNode("div", { dir: _ctx.direction }, [
      (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall59db6289d4056258.id,
        key: _ctx.$citryPrepared.calls.citryCall59db6289d4056258.key
      }, {
        ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
          _createElementVNode("div", { class: "scroll-area-nested__document" }, [
            _createElementVNode("p", null, " The deployment plan contains enough content to scroll before and after the nested inspector. "),
            _createElementVNode("p", null, " Review the service boundary, owner, and current policy before continuing to the approval section. "),
            (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallb32d05c510ac6993.id,
              key: _ctx.$citryPrepared.calls.citryCallb32d05c510ac6993.key
            }, {
              ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
                _createElementVNode("dl", { class: "scroll-area-nested__inspector" }, [
                  _createElementVNode("dt", null, "Service"),
                  _createElementVNode("dd", null, "Ledger export"),
                  _createElementVNode("dt", null, "Owner"),
                  _createElementVNode("dd", null, "Finance platform"),
                  _createElementVNode("dt", null, "Region"),
                  _createElementVNode("dd", null, "Central Europe"),
                  _createElementVNode("dt", null, "Status"),
                  _createElementVNode("dd", null, "Needs approval"),
                  _createElementVNode("dt", null, "Retention"),
                  _createElementVNode("dd", null, "Seven years"),
                  _createElementVNode("dt", null, "Encryption"),
                  _createElementVNode("dd", null, "Customer managed"),
                  _createElementVNode("dt", null, "Review"),
                  _createElementVNode("dd", null, "Quarterly")
                ])
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallf5e1b57e452853ed.id,
              key: _ctx.$citryPrepared.calls.citryCallf5e1b57e452853ed.key
            }, {
              ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
                _createElementVNode("div", { class: "scroll-area-nested__rail" }, [
                  _createElementVNode("span", null, "Plan"),
                  _createElementVNode("span", null, "Build"),
                  _createElementVNode("span", null, "Review"),
                  _createElementVNode("span", null, "Approve"),
                  _createElementVNode("span", null, "Release")
                ])
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            _createElementVNode("p", null, " Continue through the remaining deployment notes after leaving the inspector. "),
            _createElementVNode("p", null, " The outer viewport does not register the inner viewport as a widget or arbitrate its gestures. "),
            _createElementVNode("p", null, " Real wheel, precision trackpad, and touch behavior remains a platform acceptance check. ")
          ])
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ], 8 /* PROPS */, ["dir"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["12de86b576ba34208a621b681bb7d878941bb1532cc9f65bf3915866bc189d4d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb32d05c510ac6993","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf5e1b57e452853ed","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall59db6289d4056258","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":["citryCallb32d05c510ac6993","citryCallf5e1b57e452853ed"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_nested_areas_635e57be = _resolveComponent("citry-scroll-area-nested-areas-635e57be")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_nested_areas_635e57be, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall079ddf4901fb95e4.id,
      key: _ctx.$citryPrepared.calls.citryCall079ddf4901fb95e4.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3e4a99b757cba071ef67b34a31a412d58e409f3b3e00947e633fb51ce10b22bc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall079ddf4901fb95e4","typeKey":"ScrollAreaNestedAreas_985246","componentTag":"citry-scroll-area-nested-areas-635e57be","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
