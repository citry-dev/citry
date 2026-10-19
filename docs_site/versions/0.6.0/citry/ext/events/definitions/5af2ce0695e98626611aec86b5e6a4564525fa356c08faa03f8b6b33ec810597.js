(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["813ec2839f8e22774ea60a3aa5cce40ee2536816a8098ddc85050f9af752f01c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
window.__citryRuntimeDefinitions["c814387c56df99afc02fcf3d3ec0f21585ae831125b9b4076b67c3902fc5ecbe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-658ac8ee869944a7","tag":"article","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-658ac8ee869944a7","tag":"article","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, renderList: _renderList } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.citryIf0 === 0)
      ? (_openBlock(true), _createElementBlock(_Fragment, { key: 0 }, _renderList(_ctx.$citryPrepared.citryLoop0, ($citryPrepared) => {
        return (_openBlock(), _createElementBlock("span", _mergeProps({
          class: "cui-skeleton__line",
          "data-citry-ui-part": "line"
        }, $citryPrepared.citryAttrs0), null, 16 /* FULL_PROPS */))
      }), 256 /* UNKEYED_FRAGMENT */))
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["76ce7842cdebdbb76770d02a18451cdc92836d55287fc5ca8a479b1a951eaa4f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  const _component_citry_c_card_f6be905a = _resolveComponent("citry-c-card-f6be905a")
  const _component_citry_c_skeleton_89bd7275 = _resolveComponent("citry-c-skeleton-89bd7275")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-composition" }, [
    (_openBlock(), _createBlock(_component_citry_c_card_f6be905a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallf1060ba06ac5c055.id,
      key: _ctx.$citryPrepared.calls.citryCallf1060ba06ac5c055.key
    }, {
      ['citrySlot8ea89d594103a1ae']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall3bd0a5f6badefaa6.id,
          key: _ctx.$citryPrepared.calls.citryCall3bd0a5f6badefaa6.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlot9447b0af7804e094']: _withCtx(() => [
        _createElementVNode("h3", null, "Northstar Ridge")
      ]),
      ['citrySlotde2ab6e38bf88e32']: _withCtx(() => [
        _createTextVNode("A clear archive exposure from the western dome.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("article", { class: "image-composition__delayed" }, [
      _createElementVNode("h3", null, "Loading layout reservation"),
      _createElementVNode("div", { class: "image-composition__pair" }, [
        (_openBlock(), _createBlock(_component_citry_c_skeleton_89bd7275, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall801832213690f8c6.id,
          key: _ctx.$citryPrepared.calls.citryCall801832213690f8c6.key
        }, null, 8 /* PROPS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallcd2a3632bd787c58.id,
          key: _ctx.$citryPrepared.calls.citryCallcd2a3632bd787c58.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ])
    ]),
    _createElementVNode("figure", null, [
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall66039cfc032e8c75.id,
        key: _ctx.$citryPrepared.calls.citryCall66039cfc032e8c75.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("figcaption", null, "Exposure notes: 0.008 seconds at the north rim.")
    ]),
    _createElementVNode("a", {
      class: "image-composition__link",
      href: "#observation-42"
    }, [
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalld9553491f4fc5bf9.id,
        key: _ctx.$citryPrepared.calls.citryCalld9553491f4fc5bf9.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5c08370e6a4fac44ba2fb5b1284afef996f35861dfece0088ec01f8a41423ac8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3bd0a5f6badefaa6","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCallf1060ba06ac5c055","typeKey":"CCard_19daae","componentTag":"citry-c-card-f6be905a","bindings":[],"fills":[{"name":"citrySlot8ea89d594103a1ae","localDescendants":["citryCall3bd0a5f6badefaa6"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9447b0af7804e094","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotde2ab6e38bf88e32","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall801832213690f8c6","typeKey":"CSkeleton_491a4a","componentTag":"citry-c-skeleton-89bd7275","bindings":[]},{"localId":"citryCallcd2a3632bd787c58","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCall66039cfc032e8c75","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCalld9553491f4fc5bf9","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_composition_ad0b829f = _resolveComponent("citry-image-composition-ad0b829f")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_composition_ad0b829f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalldb27873a5e62047f.id,
      key: _ctx.$citryPrepared.calls.citryCalldb27873a5e62047f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["d8a4771bba412b7f75d0ea96a299806628a3554dc8bbf4249c6952b6828cf0c7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldb27873a5e62047f","typeKey":"ImageComposition_3a0106","componentTag":"citry-image-composition-ad0b829f","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
