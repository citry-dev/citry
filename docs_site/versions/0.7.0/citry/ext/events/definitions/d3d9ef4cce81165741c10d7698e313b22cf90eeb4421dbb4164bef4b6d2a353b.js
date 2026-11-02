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
      (_ctx.$citryPrepared.selectedSlots['citrySlote7cf7eb35c5daa87'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7cf7eb35c5daa87", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("img", _mergeProps({
      class: "cui-avatar__image",
      "data-citry-ui-part": "image",
      alt: ""
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4d01dc511da91814c4d0f960c470bfee11441a9799b37f53cae7fd2da9eae625"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2a85311e5fd3da999c17f91659fc201cf73e0329a94c1d9b967bf50b6e3c226f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
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
        ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["df00bf27c77ad6aa6fc5358f56cc4eea476626ce71ec719e804c775d29fdff38"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall12ee0d8f119ca449","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6619bfc5f457fd18","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall29cdff7895bb9577","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_images_3ce6c734 = _resolveComponent("citry-avatar-images-3ce6c734")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_images_3ce6c734, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6bfbdeac29b0f6c2.id,
      key: _ctx.$citryPrepared.calls.citryCall6bfbdeac29b0f6c2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["99da90fb8ec362ae0a43154c6ec5990c2203d19e2d6fadf43799c334c851f80a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6bfbdeac29b0f6c2","typeKey":"AvatarImages_39286e","componentTag":"citry-avatar-images-3ce6c734","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
