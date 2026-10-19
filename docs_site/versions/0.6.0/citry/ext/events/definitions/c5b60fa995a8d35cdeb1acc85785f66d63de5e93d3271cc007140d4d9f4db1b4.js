(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-focus" }, [
    _createElementVNode("p", null, " Tab enters the viewport before its descendants. Native scrolling keys keep focus on the viewport. "),
    (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
      onFocusin: $event => (_ctx.last=`Focused ${$event.target.id}`),
      onFocusout: $event => (_ctx.last=`Left ${$event.target.id}`),
      onScrollChange: (detail)=>
        _ctx.last=`Block offset ${Math.round(detail.blockOffset)}`,
      "citry-id": _ctx.$citryPrepared.calls.citryCallb1905281abbb2213.id,
      key: _ctx.$citryPrepared.calls.citryCallb1905281abbb2213.key
    }, {
      ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
        _createElementVNode("ol", { class: "scroll-area-focus__timeline" }, [
          _createElementVNode("li", null, [
            _createElementVNode("strong", null, "09:10"),
            _createElementVNode("span", null, "Build completed."),
            _createElementVNode("a", { href: "#build-details" }, "View build details")
          ]),
          _createElementVNode("li", null, [
            _createElementVNode("strong", null, "09:18"),
            _createElementVNode("span", null, "Security review requested."),
            (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalla9bebef97b261d14.id,
              key: _ctx.$citryPrepared.calls.citryCalla9bebef97b261d14.key
            }, {
              ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                _createTextVNode("Open review")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _createElementVNode("li", null, [
            _createElementVNode("strong", null, "09:26"),
            _createElementVNode("span", null, "Staging deployment completed."),
            _createElementVNode("a", { href: "#staging-log" }, "Read staging log")
          ]),
          _createElementVNode("li", null, [
            _createElementVNode("strong", null, "09:42"),
            _createElementVNode("span", null, "Production approval received."),
            (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall13605a5abb456212.id,
              key: _ctx.$citryPrepared.calls.citryCall13605a5abb456212.key
            }, {
              ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                _createTextVNode("Publish release")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _createElementVNode("li", null, [
            _createElementVNode("strong", null, "09:51"),
            _createElementVNode("span", null, "Release notes archived."),
            _createElementVNode("a", { href: "#release-notes" }, "Open release notes")
          ])
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onFocusin", "onFocusout", "onScrollChange", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.last)
    }, "Focus the viewport, a link, or an action", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["bd841f0345f48eb6b5b1602ede7bf23af7063b9344cabbdbe9844fd1cc28b3d8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla9bebef97b261d14","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall13605a5abb456212","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb1905281abbb2213","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"event","name":"@focusin","value":"last=`Focused ${$event.target.id}`","sourceStart":188,"sourceEnd":233},{"kind":"event","name":"@focusout","value":"last=`Left ${$event.target.id}`","sourceStart":234,"sourceEnd":277},{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n        last=`Block offset ${Math.round(detail.blockOffset)}`","sourceStart":278,"sourceEnd":368}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":["citryCall13605a5abb456212","citryCalla9bebef97b261d14"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_activity_and_focus_e5d4af9a = _resolveComponent("citry-scroll-area-activity-and-focus-e5d4af9a")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_activity_and_focus_e5d4af9a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle292901ce536f8c8.id,
      key: _ctx.$citryPrepared.calls.citryCalle292901ce536f8c8.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["06016ee82276f991b2cd2d9b43623a304f067605338a2a0652d03712bba0ff9a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle292901ce536f8c8","typeKey":"ScrollAreaActivityAndFocus_5c40e8","componentTag":"citry-scroll-area-activity-and-focus-e5d4af9a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
