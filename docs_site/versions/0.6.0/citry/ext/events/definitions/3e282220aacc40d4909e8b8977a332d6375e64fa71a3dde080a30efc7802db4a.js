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
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["62a266baa977257f3aae55e0c384bdbcb06f5a47b30a619bcf0059ef2cb8bab7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
  
  return (_openBlock(), _createElementBlock("section", {
    class: "avatar-guide",
    "aria-labelledby": "avatar-guide-title"
  }, [
    _createElementVNode("p", { class: "avatar-guide__eyebrow" }, "Moonfen field guide"),
    _createElementVNode("h2", { id: "avatar-guide-title" }, "Night expedition"),
    _createElementVNode("div", { class: "avatar-guide__row" }, [
      _createElementVNode("div", null, [
        (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall89cd591370fd7a21.id,
          key: _ctx.$citryPrepared.calls.citryCall89cd591370fd7a21.key
        }, {
          ['citrySlot242938e38ebe7959']: _withCtx(() => [
            _createTextVNode("MV")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        _createElementVNode("span", null, "Mira")
      ]),
      _createElementVNode("div", null, [
        (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall76377554b186734f.id,
          key: _ctx.$citryPrepared.calls.citryCall76377554b186734f.key
        }, {
          ['citrySlot242938e38ebe7959']: _withCtx(() => [
            _createTextVNode("OM")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        _createElementVNode("span", null, "Orrin")
      ]),
      _createElementVNode("div", null, [
        (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalle28aa4d663d20e53.id,
          key: _ctx.$citryPrepared.calls.citryCalle28aa4d663d20e53.key
        }, null, 8 /* PROPS */, ["citry-id"])),
        _createElementVNode("span", null, "Guide")
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2fc31de843a6dc78533bcafeb6c2e23d6f7ce91840f8875cca7ffc25e6ec9b09"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall89cd591370fd7a21","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall76377554b186734f","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle28aa4d663d20e53","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_at_a_glance_9ae27b02 = _resolveComponent("citry-avatar-at-a-glance-9ae27b02")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_at_a_glance_9ae27b02, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla4ac92bd352e49e8.id,
      key: _ctx.$citryPrepared.calls.citryCalla4ac92bd352e49e8.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["801d7f9652f70f668b1a500b13cc2f810059baaca079625784170293afb62e64"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla4ac92bd352e49e8","typeKey":"AvatarAtAGlance_432f44","componentTag":"citry-avatar-at-a-glance-9ae27b02","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
