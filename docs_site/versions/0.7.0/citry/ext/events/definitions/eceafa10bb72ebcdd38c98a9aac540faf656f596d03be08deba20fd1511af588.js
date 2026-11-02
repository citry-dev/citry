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
      (_ctx.$citryPrepared.selectedSlots['citrySlot87185e5de959b9d6'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot87185e5de959b9d6", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", {
      hidden: "",
      inert: "",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot3b118b957ecc918a'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot3b118b957ecc918a", { key: 1 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3366e19f39675e9b9a441db8fc3ae2163c0c276faf1eab02f0ac72f411e8dffd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6d5dd57f6ce194793a91da927bd3418dd400353843d7b5428c71f7c6e109ec2d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
          "citry-id": _ctx.$citryPrepared.calls.citryCall1303eec981a3e86d.id,
          key: _ctx.$citryPrepared.calls.citryCall1303eec981a3e86d.key
        }, {
          ['citrySlot87185e5de959b9d6']: _withCtx(() => [
            _createElementVNode("div", { class: "image-feedback__placeholder" }, [
              (_openBlock(), _createBlock(_component_citry_c_skeleton_89bd7275, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall378b67c87e5a2ff0.id,
                key: _ctx.$citryPrepared.calls.citryCall378b67c87e5a2ff0.key
              }, null, 8 /* PROPS */, ["citry-id"]))
            ])
          ]),
          ['citrySlot3b118b957ecc918a']: _withCtx(() => [
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
          "citry-id": _ctx.$citryPrepared.calls.citryCallda29d2a9a2133a15.id,
          key: _ctx.$citryPrepared.calls.citryCallda29d2a9a2133a15.key
        }, null, 8 /* PROPS */, ["citry-id"])),
        _createElementVNode("p", null, "No custom fallback is supplied, so native broken rendering and alt remain.")
      ])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b9a680b40e0361dd3c555bbcc458bf55d350da08d9b3ed3176d43957d730e1b4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall378b67c87e5a2ff0","typeKey":"CSkeleton_491a4a","componentTag":"citry-c-skeleton-89bd7275","bindings":[]},{"localId":"citryCall1303eec981a3e86d","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":src","value":"source","sourceStart":625,"sourceEnd":638},{"kind":"prop","name":":onStatusChange","value":"(detail)=>status=detail.status","sourceStart":639,"sourceEnd":687}],"fills":[{"name":"citrySlot3b118b957ecc918a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot87185e5de959b9d6","localDescendants":["citryCall378b67c87e5a2ff0"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallda29d2a9a2133a15","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_placeholder_and_error_d6fcbe3e = _resolveComponent("citry-image-placeholder-and-error-d6fcbe3e")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_placeholder_and_error_d6fcbe3e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld4d72fbebfdebee6.id,
      key: _ctx.$citryPrepared.calls.citryCalld4d72fbebfdebee6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ef66b343a6902f21e342761f21b795704ac28c7af4c8a3381d47226de36318fd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld4d72fbebfdebee6","typeKey":"ImagePlaceholderAndError_e03e57","componentTag":"citry-image-placeholder-and-error-d6fcbe3e","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
