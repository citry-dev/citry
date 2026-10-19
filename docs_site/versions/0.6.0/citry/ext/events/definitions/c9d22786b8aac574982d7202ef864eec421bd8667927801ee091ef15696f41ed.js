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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tag",
    "data-citry-ui-part": "tag"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", { class: "cui-tag__cell" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-tag__indicator",
        "data-citry-ui-part": "indicator",
        "aria-hidden": "true"
      }, _ctx.$citryPrepared.citryAttrs1), "✓", 16 /* FULL_PROPS */),
      _createElementVNode("span", {
        class: "cui-tag__start",
        "data-citry-ui-part": "start",
        "aria-hidden": "true"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot5dad434b85dafa1a'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot5dad434b85dafa1a", { key: 0 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("span", _mergeProps({
        class: "cui-tag__label",
        "data-citry-ui-part": "tag-label"
      }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot831db52320e0cc8a'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot831db52320e0cc8a", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["eed91fdc15934a18c3b09dde9d54503d2159ba7789d6da9b4eeed4fcbf3c9947"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tag-group",
    "data-citry-ui-part": "tag-group"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", _mergeProps({
      class: "cui-tag-group__label",
      "data-citry-ui-part": "group-label"
    }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      class: "cui-tag-group__list",
      "data-citry-ui-part": "list"
    }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot35ca42a839393489'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot35ca42a839393489", { key: 0 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9fad5312de33f298754309a4373dc41513ba2f6b7edd040767ae5574a8cae3d8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_avatar_59d27e85 = _resolveComponent("citry-c-avatar-59d27e85")
  const _component_citry_c_tag_a351d619 = _resolveComponent("citry-c-tag-a351d619")
  const _component_citry_c_tag_group_b31ef680 = _resolveComponent("citry-c-tag-group-b31ef680")
  
  return (_openBlock(), _createElementBlock("div", { style: "max-inline-size: 22rem" }, [
    (_openBlock(), _createBlock(_component_citry_c_tag_group_b31ef680, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0a0179be46da1b5f.id,
      key: _ctx.$citryPrepared.calls.citryCall0a0179be46da1b5f.key
    }, {
      ['citrySlot35ca42a839393489']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall63cf7d77b0c2da19.id,
          key: _ctx.$citryPrepared.calls.citryCall63cf7d77b0c2da19.key
        }, {
          ['citrySlot5dad434b85dafa1a']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall9c4a22abe7f8e753.id,
              key: _ctx.$citryPrepared.calls.citryCall9c4a22abe7f8e753.key
            }, {
              ['citrySlot242938e38ebe7959']: _withCtx(() => [
                _createTextVNode("A")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          ['citrySlot831db52320e0cc8a']: _withCtx(() => [
            _createTextVNode("Ava, accessibility research")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_tag_a351d619, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall838e437ef3d592a2.id,
          key: _ctx.$citryPrepared.calls.citryCall838e437ef3d592a2.key
        }, {
          ['citrySlot5dad434b85dafa1a']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_avatar_59d27e85, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall44ccbebca5694bf8.id,
              key: _ctx.$citryPrepared.calls.citryCall44ccbebca5694bf8.key
            }, {
              ['citrySlot242938e38ebe7959']: _withCtx(() => [
                _createTextVNode("L")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          ['citrySlot831db52320e0cc8a']: _withCtx(() => [
            _createTextVNode("Leo, design systems")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e8a8be474251756d720b929fe6b31e64f6e15b3a93dd7c1219b198437cd470b6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9c4a22abe7f8e753","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall63cf7d77b0c2da19","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot5dad434b85dafa1a","localDescendants":["citryCall9c4a22abe7f8e753"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot831db52320e0cc8a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall44ccbebca5694bf8","typeKey":"CAvatar_516550","componentTag":"citry-c-avatar-59d27e85","bindings":[],"fills":[{"name":"citrySlot242938e38ebe7959","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall838e437ef3d592a2","typeKey":"CTag_ae7eea","componentTag":"citry-c-tag-a351d619","bindings":[],"fills":[{"name":"citrySlot5dad434b85dafa1a","localDescendants":["citryCall44ccbebca5694bf8"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot831db52320e0cc8a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0a0179be46da1b5f","typeKey":"CTagGroup_765ed5","componentTag":"citry-c-tag-group-b31ef680","bindings":[],"fills":[{"name":"citrySlot35ca42a839393489","localDescendants":["citryCall44ccbebca5694bf8","citryCall63cf7d77b0c2da19","citryCall838e437ef3d592a2","citryCall9c4a22abe7f8e753"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tag_content_75277aaa = _resolveComponent("citry-tag-content-75277aaa")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tag_content_75277aaa, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfe1de1199d6d28c3.id,
      key: _ctx.$citryPrepared.calls.citryCallfe1de1199d6d28c3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["091f19626d9f22677ee4a8894283ae539384ad74de90fd691e2c6a0ea81110a1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfe1de1199d6d28c3","typeKey":"TagContent_3f886e","componentTag":"citry-tag-content-75277aaa","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
