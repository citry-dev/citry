(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-avatar",
    "data-citry-ui-part": "avatar"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-avatar__fallback",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot242938e38ebe7959'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot242938e38ebe7959", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("img", _mergeProps({
      class: "cui-avatar__image",
      "data-citry-ui-part": "image",
      alt: ""
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["85216a67f879c6d8a9d779412e391c9132b93076e58b7766e99e1984f536c94d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-avatar",
    "data-citry-ui-part": "avatar"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_openBlock(), _createElementBlock("span", {
      class: "cui-avatar__fallback",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_openBlock(), _createElementBlock("svg", {
        class: "cui-avatar__placeholder",
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        "stroke-width": "1.75",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        focusable: "false",
        "aria-hidden": "true"
      }, [
        _createElementVNode("circle", {
          cx: "12",
          cy: "8",
          r: "3.25"
        }),
        _createElementVNode("path", { d: "M5.75 19c.8-3.35 3.05-5 6.25-5s5.45 1.65 6.25 5" })
      ]))
    ]))
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1950078075590038440296851d8d4b7551292f7462b0b72d92833a7e4dbdbc2d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_avatar_59d27e85 = _resolveComponent("citry-c-avatar-59d27e85")
  
  return (_openBlock(), _createElementBlock("div", { class: "avatar-image-grid" }, [
    _createElementVNode("div", null, [
      (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall12ee0d8f119ca449.id,
        key: _ctx.$citryPrepared.calls.citryCall12ee0d8f119ca449.key
      }, {
        ['citrySlot242938e38ebe7959']: _withCtx(() => [
          _createTextVNode("FC")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("span", null, "Loaded")
    ]),
    _createElementVNode("div", null, [
      (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6619bfc5f457fd18.id,
        key: _ctx.$citryPrepared.calls.citryCall6619bfc5f457fd18.key
      }, {
        ['citrySlot242938e38ebe7959']: _withCtx(() => [
          _createTextVNode("MS")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("span", null, "Error fallback")
    ]),
    _createElementVNode("div", null, [
      (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall29cdff7895bb9577.id,
        key: _ctx.$citryPrepared.calls.citryCall29cdff7895bb9577.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("span", null, "Generic fallback")
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9a544f0f52d146729a6baa68d730370023b883782a6bfedc79b3cc25886f0b1d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall12ee0d8f119ca449","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6619bfc5f457fd18","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall29cdff7895bb9577","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_images_b8312ed6 = _resolveComponent("citry-avatar-images-b8312ed6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_images_b8312ed6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallafe51b37f2894540.id,
      key: _ctx.$citryPrepared.calls.citryCallafe51b37f2894540.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5c91be41825ea37ce0bccda72152e7cc2a01c27dabf268964a7eb1d129828efa"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallafe51b37f2894540","typeKey":"AvatarImages_0bd2f3","componentTag":"citry-avatar-images-b8312ed6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
