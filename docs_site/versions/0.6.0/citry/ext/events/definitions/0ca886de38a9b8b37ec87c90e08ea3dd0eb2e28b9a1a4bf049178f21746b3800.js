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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      hidden: "",
      inert: "",
      "aria-hidden": "true",
      "data-citry-ui-part": "placeholder"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb3a584a760bdb713'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb3a584a760bdb713", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", {
      hidden: "",
      inert: "",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot20df656fe6df3687'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot20df656fe6df3687", { key: 1 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a589546c3e2511e703b2e094e8a361bf0c66e5c2833974945ff1a348d6393936"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_skeleton_89bd7275 = _resolveComponent("citry-c-skeleton-89bd7275")
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-feedback" }, [
    _createElementVNode("div", { class: "image-feedback__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/horsehead-nebula-1280.jpg?generation=2')
      }, "Load a valid generation", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/missing-observation.jpg?generation=3')
      }, "Load a broken generation", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.source='/static/img/ui/image/horsehead-nebula-640.jpg?generation=4')
      }, "Recover with a small image", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("div", { class: "image-feedback__grid" }, [
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "Visual placeholder and fallback"),
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          src: _ctx.source,
          onStatusChange: (detail)=>_ctx.status=detail.status,
          "citry-id": _ctx.$citryPrepared.calls.citryCall5daea5f1fdaf0e29.id,
          key: _ctx.$citryPrepared.calls.citryCall5daea5f1fdaf0e29.key
        }, {
          ['citrySlotb3a584a760bdb713']: _withCtx(() => [
            _createElementVNode("div", { class: "image-feedback__placeholder" }, [
              (_openBlock(), _createBlock(_component_citry_c_skeleton_89bd7275, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall17ba9b29a5692c47.id,
                key: _ctx.$citryPrepared.calls.citryCall17ba9b29a5692c47.key
              }, null, 8 /* PROPS */, ["citry-id"]))
            ])
          ]),
          ['citrySlot20df656fe6df3687']: _withCtx(() => [
            _createElementVNode("span", { class: "image-feedback__fallback" }, "Plate unavailable")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["src", "onStatusChange", "citry-id"])),
        _createElementVNode("output", {
          textContent: _toDisplayString(`Normalized status: ${_ctx.status}`)
        }, "Normalized status: waiting", 8 /* PROPS */, ["textContent"])
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "Native broken-image fallback"),
        (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalla31314bc0855e956.id,
          key: _ctx.$citryPrepared.calls.citryCalla31314bc0855e956.key
        }, null, 8 /* PROPS */, ["citry-id"])),
        _createElementVNode("p", null, "No custom fallback is supplied, so native broken rendering and alt remain.")
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["45f46713154ab2ca7ff292a1de7663fdc00be3759fe4b9d64a1506561fb78523"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall17ba9b29a5692c47","typeKey":"CSkeleton_491a4a","componentTag":"citry-c-skeleton-89bd7275","bindings":[]},{"localId":"citryCall5daea5f1fdaf0e29","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":src","value":"source","sourceStart":625,"sourceEnd":638},{"kind":"prop","name":":onStatusChange","value":"(detail)=>status=detail.status","sourceStart":639,"sourceEnd":687}],"fills":[{"name":"citrySlot20df656fe6df3687","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb3a584a760bdb713","localDescendants":["citryCall17ba9b29a5692c47"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla31314bc0855e956","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_placeholder_and_error_b21fb8e9 = _resolveComponent("citry-image-placeholder-and-error-b21fb8e9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_placeholder_and_error_b21fb8e9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallacaa010ad905a1b9.id,
      key: _ctx.$citryPrepared.calls.citryCallacaa010ad905a1b9.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["bde16f6d48729f0729a107bad89f985c3bfcde6b2866c85f7bdb419c5ae0d620"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallacaa010ad905a1b9","typeKey":"ImagePlaceholderAndError_9e626a","componentTag":"citry-image-placeholder-and-error-b21fb8e9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
