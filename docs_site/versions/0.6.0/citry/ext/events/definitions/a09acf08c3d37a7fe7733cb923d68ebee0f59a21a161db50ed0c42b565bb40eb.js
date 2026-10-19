(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-658ac8ee869944a7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("div", {
      class: "cui-card__media",
      "data-citry-ui-part": "media"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot8ea89d594103a1ae'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot8ea89d594103a1ae", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "header" }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("div", { class: "cui-card__header-content" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot9447b0af7804e094'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot9447b0af7804e094", { key: 1 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", {
      class: "cui-card__body",
      "data-citry-ui-part": "body"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotde2ab6e38bf88e32'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotde2ab6e38bf88e32", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["070799b3767b912e94c4b1fd98b50f62a514603154359205a9465fa6b358aed1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-658ac8ee869944a7","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-658ac8ee869944a7","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_card_f6be905a = _resolveComponent("citry-c-card-f6be905a")
  
  return (_openBlock(), _createElementBlock("section", { class: "card-media" }, [
    (_openBlock(), _createBlock(_component_citry_c_card_f6be905a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0871fe04793e4f0b.id,
      key: _ctx.$citryPrepared.calls.citryCall0871fe04793e4f0b.key
    }, {
      ['citrySlot8ea89d594103a1ae']: _withCtx(() => [
        (_openBlock(), _createElementBlock("svg", {
          class: "card-media__illustration",
          viewBox: "0 0 360 190",
          role: "img",
          "aria-label": "A round table beside a sunlit arched window"
        }, [
          _createElementVNode("rect", {
            width: "360",
            height: "190",
            fill: "#d9c5a3"
          }),
          _createElementVNode("path", {
            d: "M220 170V70a58 58 0 0 1 116 0v100",
            fill: "#8da7a0"
          }),
          _createElementVNode("circle", {
            cx: "278",
            cy: "70",
            r: "38",
            fill: "#f7e7a7",
            opacity: ".8"
          }),
          _createElementVNode("ellipse", {
            cx: "105",
            cy: "135",
            rx: "72",
            ry: "18",
            fill: "#7a4e32"
          }),
          _createElementVNode("path", {
            d: "M84 135v42M126 135v42",
            stroke: "#513523",
            "stroke-width": "8"
          })
        ]))
      ]),
      ['citrySlot9447b0af7804e094']: _withCtx(() => [
        _createElementVNode("h2", null, "Breakfast nook")
      ]),
      ['citrySlotde2ab6e38bf88e32']: _withCtx(() => [
        _createTextVNode(" Card preserves the illustration's own aspect ratio and accessible name. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_card_f6be905a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla88bf68d010270b9.id,
      key: _ctx.$citryPrepared.calls.citryCalla88bf68d010270b9.key
    }, {
      ['citrySlot8ea89d594103a1ae']: _withCtx(() => [
        _createElementVNode("div", { class: "card-media__swatches" }, [
          _createElementVNode("span", { class: "card-media__clay" }, "Clay"),
          _createElementVNode("span", { class: "card-media__linen" }, "Linen"),
          _createElementVNode("span", { class: "card-media__moss" }, "Moss"),
          _createElementVNode("span", { class: "card-media__walnut" }, "Walnut")
        ])
      ]),
      ['citrySlot9447b0af7804e094']: _withCtx(() => [
        _createElementVNode("h2", null, "Autumn materials")
      ]),
      ['citrySlotde2ab6e38bf88e32']: _withCtx(() => [
        _createTextVNode(" Multiple consumer-owned nodes can define their own media layout. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2a8ffd35c142923b73e160d36ae1dc1abe3414992e9936fb155c35c40a78b919"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0871fe04793e4f0b","typeKey":"CCard_19daae","componentTag":"citry-c-card-f6be905a","bindings":[],"fills":[{"name":"citrySlot8ea89d594103a1ae","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9447b0af7804e094","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotde2ab6e38bf88e32","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla88bf68d010270b9","typeKey":"CCard_19daae","componentTag":"citry-c-card-f6be905a","bindings":[],"fills":[{"name":"citrySlot8ea89d594103a1ae","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9447b0af7804e094","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotde2ab6e38bf88e32","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_card_media_6275be66 = _resolveComponent("citry-card-media-6275be66")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_card_media_6275be66, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla95c96cbf3afe12b.id,
      key: _ctx.$citryPrepared.calls.citryCalla95c96cbf3afe12b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["7ef59738d44fb231727ffcfec94b7edb5216bf41021ca11e88ef53127b9290d6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla95c96cbf3afe12b","typeKey":"CardMedia_1603f2","componentTag":"citry-card-media-6275be66","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
