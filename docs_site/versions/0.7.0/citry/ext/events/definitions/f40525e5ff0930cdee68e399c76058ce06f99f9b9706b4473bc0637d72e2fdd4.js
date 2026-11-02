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
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b96277b515ed108195a76b351c5a2eed4418ed0a5d7773c33d7a9a5a00908156"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
          ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
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
          ['citrySlote7cf7eb35c5daa87']: _withCtx(() => [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3fc21b7db589c207d1692dbbf10d440e9b8669d445e7e3314ec3b2a0c2246aab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall89cd591370fd7a21","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall76377554b186734f","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlote7cf7eb35c5daa87","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle28aa4d663d20e53","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_avatar_at_a_glance_4bf8c717 = _resolveComponent("citry-avatar-at-a-glance-4bf8c717")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_avatar_at_a_glance_4bf8c717, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6f0a86efaaf9a960.id,
      key: _ctx.$citryPrepared.calls.citryCall6f0a86efaaf9a960.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d5d2dc59ad56e0972da31ddf99442e22b5db9bbe4cb65434129c067c26a33a56"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6f0a86efaaf9a960","typeKey":"AvatarAtAGlance_a246a5","componentTag":"citry-avatar-at-a-glance-4bf8c717","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
