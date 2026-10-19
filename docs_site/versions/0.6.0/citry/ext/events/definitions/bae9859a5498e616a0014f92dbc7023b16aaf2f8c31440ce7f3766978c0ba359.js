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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-lifecycle" }, [
    _createElementVNode("div", { class: "image-lifecycle__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent6a', $event))
      }, "Retain equal server output", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEventba', $event))
      }, "Change the resource", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent10c', $event))
      }, "Replace native ownership", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent15b', $event))
      }, "Remove the Image", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent1a1', $event))
      }, "Restore a fresh Image", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent1ed', $event))
      }, "Remove it again", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent238', $event))
      }, "Restore it again", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {
        const root=_ctx.$root.querySelector('#image-lifecycle-target');
        if (root) root.setAttribute('data-status','forged');
      }
      }, "Test hostile status fail-closed", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {
        const root=_ctx.$root.querySelector('#image-lifecycle-target');
        if (root) root.after(root.cloneNode(true));
      }
      }, "Insert an unowned clone", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("p", null, [
      _createTextVNode("Signed server step: "),
      _createElementVNode("output", { "data-image-lifecycle-step": "" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ]),
    (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
      onStatusChange: (detail)=>{
          _ctx.status=detail.status;
          _ctx.selected=(detail.current_src || detail.src).split('/').pop().split('?')[0];
        },
      "citry-id": _ctx.$citryPrepared.calls.citryCall02068f8926f39a2a.id,
      key: _ctx.$citryPrepared.calls.citryCall02068f8926f39a2a.key
    }, {
      ['citrySlotb3a584a760bdb713']: _withCtx(() => [
        _createTextVNode("Loading calibration plate")
      ]),
      ['citrySlot20df656fe6df3687']: _withCtx(() => [
        _createTextVNode("Calibration plate unavailable")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onStatusChange", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Status ${_ctx.status}; selected ${_ctx.selected}`)
    }, " Status waiting; selected none ", 8 /* PROPS */, ["textContent"]),
    _createElementVNode("div", {
      id: "image-lifecycle-shadow-host",
      "aria-label": "Open ShadowRoot move fixture"
    })
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["273154d92667ab45d099ad3c416870b03ec305c8740c61a192076ae97eef161d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall02068f8926f39a2a","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":onStatusChange","value":"(detail)=>{\n          status=detail.status;\n          selected=(detail.current_src || detail.src).split('/').pop().split('?')[0];\n        }","sourceStart":1507,"sourceEnd":1664}],"fills":[{"name":"citrySlot20df656fe6df3687","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotb3a584a760bdb713","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_lifecycle_fb6ca892 = _resolveComponent("citry-image-lifecycle-fb6ca892")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_lifecycle_fb6ca892, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7955893eaf66ff21.id,
      key: _ctx.$citryPrepared.calls.citryCall7955893eaf66ff21.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5d7c177d18973ecf0f12492cefca4dd27b3ff2d59ab9f15a39e44549ed34335b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7955893eaf66ff21","typeKey":"ImageLifecycle_381cb3","componentTag":"citry-image-lifecycle-fb6ca892","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
