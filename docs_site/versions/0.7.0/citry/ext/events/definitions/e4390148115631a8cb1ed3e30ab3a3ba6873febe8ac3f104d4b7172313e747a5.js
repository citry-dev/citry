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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fc5946de71210d0226a09c473d0d70ccc9386d6b8ae8a7c7335e50a95ac4f7da"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    (_ctx.$citryPrepared.selectedSlots['citrySloteccae598065f9beb'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySloteccae598065f9beb", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5a87120f1eb82c6282bd28df216e228693452217816036d2f417585763cb4833"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("section", _mergeProps({
    class: "cui-carousel",
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
        (_ctx.$citryPrepared.selectedSlots['citrySlot3ad108533a7a7e5c'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot3ad108533a7a7e5c", { key: 0 })
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ed8ec44d53940707ad73d34a00323242343b97fd3c95b079ca37b9193658fdf7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  const _component_citry_c_carousel_slide_fc4a58d3 = _resolveComponent("citry-c-carousel-slide-fc4a58d3")
  const _component_citry_c_carousel_b3909dca = _resolveComponent("citry-c-carousel-b3909dca")
  
  return (_openBlock(), _createBlock(_component_citry_c_carousel_b3909dca, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallf52b4edb19c618d5.id,
    key: _ctx.$citryPrepared.calls.citryCallf52b4edb19c618d5.key
  }, {
    ['citrySlot3ad108533a7a7e5c']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1b2226520d27fff5.id,
        key: _ctx.$citryPrepared.calls.citryCall1b2226520d27fff5.key
      }, {
        ['citrySloteccae598065f9beb']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall18a3217e7f802929.id,
            key: _ctx.$citryPrepared.calls.citryCall18a3217e7f802929.key
          }, {
            ['citrySlotc35871f9572748e0']: _withCtx(() => [
              _createTextVNode("Morning observations")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallb88a0b8734f8b12d.id,
        key: _ctx.$citryPrepared.calls.citryCallb88a0b8734f8b12d.key
      }, {
        ['citrySloteccae598065f9beb']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall6a4074dcbaac78f5.id,
            key: _ctx.$citryPrepared.calls.citryCall6a4074dcbaac78f5.key
          }, {
            ['citrySlotc35871f9572748e0']: _withCtx(() => [
              _createTextVNode("Evening observations")
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d8fd9467f4908a15dad504f043864eed97cb4ef27165e1d13b1265c4b5913fde"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall18a3217e7f802929","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1b2226520d27fff5","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySloteccae598065f9beb","localDescendants":["citryCall18a3217e7f802929"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6a4074dcbaac78f5","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb88a0b8734f8b12d","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySloteccae598065f9beb","localDescendants":["citryCall6a4074dcbaac78f5"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf52b4edb19c618d5","typeKey":"CCarousel_f351c4","componentTag":"citry-c-carousel-b3909dca","bindings":[],"fills":[{"name":"citrySlot3ad108533a7a7e5c","localDescendants":["citryCall18a3217e7f802929","citryCall1b2226520d27fff5","citryCall6a4074dcbaac78f5","citryCallb88a0b8734f8b12d"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_vertical_carousel_d4fbcb58 = _resolveComponent("citry-vertical-carousel-d4fbcb58")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_vertical_carousel_d4fbcb58, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4e1b0667ae4047f3.id,
      key: _ctx.$citryPrepared.calls.citryCall4e1b0667ae4047f3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a084b5a48627bf949ffbbf4d73c2f16e6a37d1c908f6a22a65899a7edfea5b61"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4e1b0667ae4047f3","typeKey":"VerticalCarousel_f4dfd1","componentTag":"citry-vertical-carousel-d4fbcb58","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
