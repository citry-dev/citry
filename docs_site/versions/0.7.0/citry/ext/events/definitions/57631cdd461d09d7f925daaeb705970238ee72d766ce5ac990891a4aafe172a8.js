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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6d5dd57f6ce194793a91da927bd3418dd400353843d7b5428c71f7c6e109ec2d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["12835744e6539bdb0ce8ff12802071f8b92d2ebdc821f354bcae9279bfdb4948"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-658ac8ee869944a7","tag":"article","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["622bed7442999812ae214c6c9fc3b5f04816f2b4522e26360c37353e3767b3f1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["134615b4111f6db23bf45cdd31ed2be8fb91933b96436da850a014c420359c65"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3bd0a5f6badefaa6","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCallf1060ba06ac5c055","typeKey":"CCard_19daae","componentTag":"citry-c-card-f6be905a","bindings":[],"fills":[{"name":"citrySlot8ea89d594103a1ae","localDescendants":["citryCall3bd0a5f6badefaa6"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot9447b0af7804e094","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotde2ab6e38bf88e32","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall801832213690f8c6","typeKey":"CSkeleton_491a4a","componentTag":"citry-c-skeleton-89bd7275","bindings":[]},{"localId":"citryCallcd2a3632bd787c58","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCall66039cfc032e8c75","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCalld9553491f4fc5bf9","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_composition_da178761 = _resolveComponent("citry-image-composition-da178761")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_composition_da178761, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5f312be221b83e2d.id,
      key: _ctx.$citryPrepared.calls.citryCall5f312be221b83e2d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1072189992ff6dc61d4a52d00166de6c530bce568bcb1d70877a51eabba85543"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5f312be221b83e2d","typeKey":"ImageComposition_657e7f","componentTag":"citry-image-composition-da178761","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
