(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-alert",
    "data-citry-ui-part": "alert"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_openBlock(), _createElementBlock("div", {
      class: "cui-alert__indicator",
      "aria-hidden": "true",
      "data-citry-ui-part": "indicator"
    }, [
      (_openBlock(), _createElementBlock("svg", {
        class: "cui-alert__icon",
        xmlns: "http://www.w3.org/2000/svg",
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        focusable: "false",
        "aria-hidden": "true"
      }, [
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "M12 16v-4" }),
          _createElementVNode("path", { d: "M12 8h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m9 12 2 2 4-4" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs3)), [
          _createElementVNode("path", { d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" }),
          _createElementVNode("path", { d: "M12 9v4" }),
          _createElementVNode("path", { d: "M12 17h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m15 9-6 6" }),
          _createElementVNode("path", { d: "m9 9 6 6" })
        ], 16 /* FULL_PROPS */)
      ]))
    ])),
    _createElementVNode("div", {
      class: "cui-alert__content",
      "data-citry-ui-part": "content"
    }, [
      _createElementVNode("div", {
        class: "cui-alert__message",
        "data-citry-ui-part": "message"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotc35871f9572748e0'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotc35871f9572748e0", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cfd1cee44a47ed0d1489a52019304f00209819201262aef64a76d01588e18535"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-carousel__slide",
    role: "group",
    "data-citry-carousel-slide": "",
    "data-citry-ui-part": "slide"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot71c1c6dae5147e80'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot71c1c6dae5147e80", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4d5b969beee9a9e20b9ceb1803275c56a3f958442f78e758291e0b7fee9beba6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("section", _mergeProps({
    role: "region",
    "data-citry-carousel-root": "",
    "data-citry-ui-part": "carousel"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", { "data-citry-ui-part": "controls" }, [
      _createElementVNode("button", _mergeProps({
        type: "button",
        "data-citry-carousel-previous": "",
        "data-citry-ui-part": "previous"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("span", { "aria-hidden": "true" }, "←")
      ], 16 /* FULL_PROPS */),
      _createElementVNode("button", _mergeProps({
        type: "button",
        "data-citry-carousel-next": "",
        "data-citry-ui-part": "next"
      }, _ctx.$citryPrepared.citryAttrs2), [
        _createElementVNode("span", { "aria-hidden": "true" }, "→")
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("div", {
      tabindex: "0",
      "data-citry-carousel-viewport": "",
      "data-citry-ui-part": "viewport"
    }, [
      _createElementVNode("div", { "data-citry-ui-part": "track" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotd620348e8d7eaa6d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotd620348e8d7eaa6d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ]),
    _createElementVNode("div", _mergeProps({
      role: "group",
      "data-citry-carousel-indicators": "",
      "data-citry-ui-part": "indicators"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fa64b6bf57017156fc61718dc893058e9252b149a3add5ffffb02e2bfd975c99"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  const _component_citry_c_carousel_slide_fc4a58d3 = _resolveComponent("citry-c-carousel-slide-fc4a58d3")
  const _component_citry_c_carousel_b3909dca = _resolveComponent("citry-c-carousel-b3909dca")
  
  return (_openBlock(), _createBlock(_component_citry_c_carousel_b3909dca, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallf1ded37ad0b8f4bb.id,
    key: _ctx.$citryPrepared.calls.citryCallf1ded37ad0b8f4bb.key
  }, {
    ['citrySlotd620348e8d7eaa6d']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall99f4293873bbeab0.id,
        key: _ctx.$citryPrepared.calls.citryCall99f4293873bbeab0.key
      }, {
        ['citrySlot71c1c6dae5147e80']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall4580bab66bde5e27.id,
            key: _ctx.$citryPrepared.calls.citryCall4580bab66bde5e27.key
          }, {
            ['citrySlotc35871f9572748e0']: _withCtx(() => [
              _createTextVNode("The northern ridge at blue hour.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf85d5f5eca31db38.id,
        key: _ctx.$citryPrepared.calls.citryCallf85d5f5eca31db38.key
      }, {
        ['citrySlot71c1c6dae5147e80']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall2f28dfbbe056702c.id,
            key: _ctx.$citryPrepared.calls.citryCall2f28dfbbe056702c.key
          }, {
            ['citrySlotc35871f9572748e0']: _withCtx(() => [
              _createTextVNode("Reflections on the glacial lake.")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["87635136c95d53b8fe637e720a96979f84c23118b716d0030cac55d5ac0afed7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4580bab66bde5e27","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall99f4293873bbeab0","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySlot71c1c6dae5147e80","localDescendants":["citryCall4580bab66bde5e27"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2f28dfbbe056702c","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf85d5f5eca31db38","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySlot71c1c6dae5147e80","localDescendants":["citryCall2f28dfbbe056702c"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf1ded37ad0b8f4bb","typeKey":"CCarousel_f351c4","componentTag":"citry-c-carousel-b3909dca","bindings":[],"fills":[{"name":"citrySlotd620348e8d7eaa6d","localDescendants":["citryCall2f28dfbbe056702c","citryCall4580bab66bde5e27","citryCall99f4293873bbeab0","citryCallf85d5f5eca31db38"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_custom_carousel_425cf47d = _resolveComponent("citry-custom-carousel-425cf47d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_custom_carousel_425cf47d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld5eafb927b78d377.id,
      key: _ctx.$citryPrepared.calls.citryCalld5eafb927b78d377.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["67308d3a7bd7fc76dd766e008433129ebe9c6a8e777413632b2725913bcd45cc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld5eafb927b78d377","typeKey":"CustomCarousel_552c53","componentTag":"citry-custom-carousel-425cf47d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
