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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-direction" }, [
    _createElementVNode("div", { class: "scroll-area-direction__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.direction=_ctx.direction === 'ltr' ? 'rtl' : 'ltr')
      }, "Flip the third rail", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        textContent: _toDisplayString(`Third rail direction: ${_ctx.direction}`)
      }, " Third rail direction: ltr ", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("div", { class: "scroll-area-direction__grid" }, [
      _createElementVNode("article", { dir: "ltr" }, [
        _createElementVNode("h3", null, "LTR"),
        (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
          onScrollChange: (detail)=>
            _ctx.ltrOffset=Math.round(detail.inlineOffset),
          "citry-id": _ctx.$citryPrepared.calls.citryCall86ad5a747b39b3cb.id,
          key: _ctx.$citryPrepared.calls.citryCall86ad5a747b39b3cb.key
        }, {
          ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
            _createElementVNode("div", { class: "scroll-area-direction__rail" }, [
              _createElementVNode("span", null, "Plan"),
              _createElementVNode("span", null, "Build"),
              _createElementVNode("span", null, "Review"),
              _createElementVNode("span", null, "Approve"),
              _createElementVNode("span", null, "Publish"),
              _createElementVNode("span", null, "Archive")
            ])
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onScrollChange", "citry-id"])),
        _createElementVNode("output", {
          textContent: _toDisplayString(`Logical offset ${_ctx.ltrOffset}`)
        }, " Logical offset 0 ", 8 /* PROPS */, ["textContent"])
      ]),
      _createElementVNode("article", { dir: "rtl" }, [
        _createElementVNode("h3", null, "RTL"),
        (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
          onScrollChange: (detail)=>
            _ctx.rtlOffset=Math.round(detail.inlineOffset),
          "citry-id": _ctx.$citryPrepared.calls.citryCall93c77908bbea5c01.id,
          key: _ctx.$citryPrepared.calls.citryCall93c77908bbea5c01.key
        }, {
          ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
            _createElementVNode("div", { class: "scroll-area-direction__rail" }, [
              _createElementVNode("span", null, "تخطيط"),
              _createElementVNode("span", null, "بناء"),
              _createElementVNode("span", null, "مراجعة"),
              _createElementVNode("span", null, "موافقة"),
              _createElementVNode("span", null, "نشر"),
              _createElementVNode("span", null, "أرشفة")
            ])
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onScrollChange", "citry-id"])),
        _createElementVNode("output", {
          textContent: _toDisplayString(`Logical offset ${_ctx.rtlOffset}`)
        }, " Logical offset 0 ", 8 /* PROPS */, ["textContent"])
      ]),
      _createElementVNode("article", { dir: _ctx.direction }, [
        _createElementVNode("h3", null, "Direction change"),
        (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
          onScrollChange: (detail)=>
            _ctx.flipOffset=Math.round(detail.inlineOffset),
          "citry-id": _ctx.$citryPrepared.calls.citryCall1bae2fb5edb22a97.id,
          key: _ctx.$citryPrepared.calls.citryCall1bae2fb5edb22a97.key
        }, {
          ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
            _createElementVNode("div", { class: "scroll-area-direction__rail" }, [
              _createElementVNode("span", null, "North"),
              _createElementVNode("span", null, "South"),
              _createElementVNode("span", null, "East"),
              _createElementVNode("span", null, "West"),
              _createElementVNode("span", null, "Coast"),
              _createElementVNode("span", null, "Harbor")
            ])
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onScrollChange", "citry-id"])),
        _createElementVNode("output", {
          textContent: _toDisplayString(`Logical offset ${_ctx.flipOffset}`)
        }, " Logical offset 0 ", 8 /* PROPS */, ["textContent"])
      ], 8 /* PROPS */, ["dir"])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c863ed7a0b71617556578033d39b7b7b222ab6df59bb8d9c41535076a92cdf4c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall86ad5a747b39b3cb","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            ltrOffset=Math.round(detail.inlineOffset)","sourceStart":437,"sourceEnd":519}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall93c77908bbea5c01","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            rtlOffset=Math.round(detail.inlineOffset)","sourceStart":1128,"sourceEnd":1210}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1bae2fb5edb22a97","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            flipOffset=Math.round(detail.inlineOffset)","sourceStart":1861,"sourceEnd":1944}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_rtl_and_direction_33809584 = _resolveComponent("citry-scroll-area-rtl-and-direction-33809584")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_rtl_and_direction_33809584, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall8f2c0391bbaa7f10.id,
      key: _ctx.$citryPrepared.calls.citryCall8f2c0391bbaa7f10.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d9c333b23270082d37f80ab48adcb0b5bfe4f9b59ce7c62a91e308caaf6c159e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8f2c0391bbaa7f10","typeKey":"ScrollAreaRtlAndDirection_c23742","componentTag":"citry-scroll-area-rtl-and-direction-33809584","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
