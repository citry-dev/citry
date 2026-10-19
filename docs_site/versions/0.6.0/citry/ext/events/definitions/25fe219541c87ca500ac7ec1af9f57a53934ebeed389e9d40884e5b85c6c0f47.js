(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("li", {
    class: "cui-list-item",
    "data-citry-ui-part": "list-item"
  }, [
    _createElementVNode("div", { "data-citry-ui-part": "surface" }, [
      _createElementVNode("div", { "data-citry-ui-part": "body" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot9cded70e690c64ab'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot9cded70e690c64ab", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["7093dde4ab803247f4fcbee945e387fbd45fab5733425fb7883c7f34208b4109"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("ol", _mergeProps({
    class: "cui-list",
    "data-citry-ui-part": "list"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot6316ab03430682a9'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot6316ab03430682a9", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f2878aa01571ab0b06f5c1660a86b4620e13442c8c1392564c0d2073965429fd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_list_item_ebec2f07 = _resolveComponent("citry-c-list-item-ebec2f07")
  const _component_citry_c_list_170fd5a5 = _resolveComponent("citry-c-list-170fd5a5")
  
  return (_openBlock(), _createBlock(_component_citry_c_list_170fd5a5, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall0268e583a2419283.id,
    key: _ctx.$citryPrepared.calls.citryCall0268e583a2419283.key
  }, {
    ['citrySlot6316ab03430682a9']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_list_item_ebec2f07, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall76e94b0f0cef15ff.id,
        key: _ctx.$citryPrepared.calls.citryCall76e94b0f0cef15ff.key
      }, {
        ['citrySlot9cded70e690c64ab']: _withCtx(() => [
          _createTextVNode("Align the telescope")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_list_item_ebec2f07, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalld0a89e8cb6f7dbcf.id,
        key: _ctx.$citryPrepared.calls.citryCalld0a89e8cb6f7dbcf.key
      }, {
        ['citrySlot9cded70e690c64ab']: _withCtx(() => [
          _createTextVNode("Calibrate the camera")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_list_item_ebec2f07, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall21d87ea9fb6536b0.id,
        key: _ctx.$citryPrepared.calls.citryCall21d87ea9fb6536b0.key
      }, {
        ['citrySlot9cded70e690c64ab']: _withCtx(() => [
          _createTextVNode("Begin the exposure")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6c70fc166c79d44442667bce19e7d049f99620b49182cfabe8b3c76d050f6656"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall76e94b0f0cef15ff","typeKey":"CListItem_4d2caa","componentTag":"citry-c-list-item-ebec2f07","bindings":[],"fills":[{"name":"citrySlot9cded70e690c64ab","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld0a89e8cb6f7dbcf","typeKey":"CListItem_4d2caa","componentTag":"citry-c-list-item-ebec2f07","bindings":[],"fills":[{"name":"citrySlot9cded70e690c64ab","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall21d87ea9fb6536b0","typeKey":"CListItem_4d2caa","componentTag":"citry-c-list-item-ebec2f07","bindings":[],"fills":[{"name":"citrySlot9cded70e690c64ab","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0268e583a2419283","typeKey":"CList_34f50c","componentTag":"citry-c-list-170fd5a5","bindings":[],"fills":[{"name":"citrySlot6316ab03430682a9","localDescendants":["citryCall21d87ea9fb6536b0","citryCall76e94b0f0cef15ff","citryCalld0a89e8cb6f7dbcf"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_list_content_3b474231 = _resolveComponent("citry-list-content-3b474231")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_list_content_3b474231, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2681c20476b63db4.id,
      key: _ctx.$citryPrepared.calls.citryCall2681c20476b63db4.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5122c002e946657e36baa4c25abef053b945e3ec2fe53378167388358d3f10d7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2681c20476b63db4","typeKey":"ListContent_35897c","componentTag":"citry-list-content-3b474231","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
