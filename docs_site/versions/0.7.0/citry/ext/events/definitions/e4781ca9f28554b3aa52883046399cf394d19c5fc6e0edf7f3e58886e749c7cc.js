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
window.__citryRuntimeDefinitions["531dcc8b661c63a397c414f19e57cf683e683728fd470f354cd2ab2200bb731f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall86ad5a747b39b3cb","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            ltrOffset=Math.round(detail.inlineOffset)","sourceStart":437,"sourceEnd":519}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall93c77908bbea5c01","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            rtlOffset=Math.round(detail.inlineOffset)","sourceStart":1128,"sourceEnd":1210}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1bae2fb5edb22a97","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            flipOffset=Math.round(detail.inlineOffset)","sourceStart":1861,"sourceEnd":1944}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_rtl_and_direction_188580a9 = _resolveComponent("citry-scroll-area-rtl-and-direction-188580a9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_rtl_and_direction_188580a9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall69e07a92e81041fa.id,
      key: _ctx.$citryPrepared.calls.citryCall69e07a92e81041fa.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["87829b2ffee5d1f4906a9e3d153be406bec20a312366b5535dd133b0a50a9383"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall69e07a92e81041fa","typeKey":"ScrollAreaRtlAndDirection_d103f0","componentTag":"citry-scroll-area-rtl-and-direction-188580a9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
