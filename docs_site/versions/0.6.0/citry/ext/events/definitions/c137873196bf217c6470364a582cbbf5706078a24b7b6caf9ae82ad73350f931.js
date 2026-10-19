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
window.__citryRuntimeDefinitions["b73d02a5e73a57629387e0c035b62ce5adb621d59570a6e77882741b988d422f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  const _component_citry_c_carousel_slide_fc4a58d3 = _resolveComponent("citry-c-carousel-slide-fc4a58d3")
  const _component_citry_c_carousel_b3909dca = _resolveComponent("citry-c-carousel-b3909dca")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createTextVNode("Slide "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.index + 1)
      }, null, 8 /* PROPS */, ["textContent"]),
      _createTextVNode(" of 3")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_carousel_b3909dca, {
      index: _ctx.index,
      onIndexChange: (next)=>_ctx.index=next,
      "citry-id": _ctx.$citryPrepared.calls.citryCall1eef0c160afbea07.id,
      key: _ctx.$citryPrepared.calls.citryCall1eef0c160afbea07.key
    }, {
      ['citrySlotd620348e8d7eaa6d']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall0649ce51f23a3b65.id,
          key: _ctx.$citryPrepared.calls.citryCall0649ce51f23a3b65.key
        }, {
          ['citrySlot71c1c6dae5147e80']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallc2dc2408cee8a71d.id,
              key: _ctx.$citryPrepared.calls.citryCallc2dc2408cee8a71d.key
            }, {
              ['citrySlotc35871f9572748e0']: _withCtx(() => [
                _createTextVNode("First controlled Slide")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1f8fde1d5f60ea24.id,
          key: _ctx.$citryPrepared.calls.citryCall1f8fde1d5f60ea24.key
        }, {
          ['citrySlot71c1c6dae5147e80']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall2bdf45094632b5ee.id,
              key: _ctx.$citryPrepared.calls.citryCall2bdf45094632b5ee.key
            }, {
              ['citrySlotc35871f9572748e0']: _withCtx(() => [
                _createTextVNode("Second controlled Slide")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_carousel_slide_fc4a58d3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall83f5c03481193fe6.id,
          key: _ctx.$citryPrepared.calls.citryCall83f5c03481193fe6.key
        }, {
          ['citrySlot71c1c6dae5147e80']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall9335eea95fb95fab.id,
              key: _ctx.$citryPrepared.calls.citryCall9335eea95fb95fab.key
            }, {
              ['citrySlotc35871f9572748e0']: _withCtx(() => [
                _createTextVNode("Third controlled Slide")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["index", "onIndexChange", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1745e951d29e387bfaf6b6d5bf076ff5425e8e1562304c4a4cfb123c988ebf15"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc2dc2408cee8a71d","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0649ce51f23a3b65","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySlot71c1c6dae5147e80","localDescendants":["citryCallc2dc2408cee8a71d"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2bdf45094632b5ee","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1f8fde1d5f60ea24","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySlot71c1c6dae5147e80","localDescendants":["citryCall2bdf45094632b5ee"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9335eea95fb95fab","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall83f5c03481193fe6","typeKey":"CCarouselSlide_3aa95b","componentTag":"citry-c-carousel-slide-fc4a58d3","bindings":[],"fills":[{"name":"citrySlot71c1c6dae5147e80","localDescendants":["citryCall9335eea95fb95fab"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1eef0c160afbea07","typeKey":"CCarousel_f351c4","componentTag":"citry-c-carousel-b3909dca","bindings":[{"kind":"prop","name":":index","value":"index","sourceStart":91,"sourceEnd":105},{"kind":"prop","name":":onIndexChange","value":"(next)=>index=next","sourceStart":106,"sourceEnd":141}],"fills":[{"name":"citrySlotd620348e8d7eaa6d","localDescendants":["citryCall0649ce51f23a3b65","citryCall1f8fde1d5f60ea24","citryCall2bdf45094632b5ee","citryCall83f5c03481193fe6","citryCall9335eea95fb95fab","citryCallc2dc2408cee8a71d"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_carousel_02cf10d0 = _resolveComponent("citry-controlled-carousel-02cf10d0")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_carousel_02cf10d0, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla5312682bdee517d.id,
      key: _ctx.$citryPrepared.calls.citryCalla5312682bdee517d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ddc1a76384ef41cd315989ece5ae013efc0e35f20f93a5361fbe6315d8b3594c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla5312682bdee517d","typeKey":"ControlledCarousel_08a063","componentTag":"citry-controlled-carousel-02cf10d0","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
