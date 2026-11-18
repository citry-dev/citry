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
      onStatusChange: _ctx.recordStatus,
      "citry-id": _ctx.$citryPrepared.calls.citryCallf1ba14fdde3302be.id,
      key: _ctx.$citryPrepared.calls.citryCallf1ba14fdde3302be.key
    }, {
      ['citrySlot87185e5de959b9d6']: _withCtx(() => [
        _createTextVNode("Loading calibration plate")
      ]),
      ['citrySlot3b118b957ecc918a']: _withCtx(() => [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3fcb0e04b9cbcbdca4742d395147d9583d9d5f48eeab85ee69e682a562629468"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf1ba14fdde3302be","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[{"kind":"prop","name":":onStatusChange","value":"recordStatus","sourceStart":1507,"sourceEnd":1537}],"fills":[{"name":"citrySlot3b118b957ecc918a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot87185e5de959b9d6","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_lifecycle_461b25b0 = _resolveComponent("citry-image-lifecycle-461b25b0")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_lifecycle_461b25b0, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb3112c2a8702c67f.id,
      key: _ctx.$citryPrepared.calls.citryCallb3112c2a8702c67f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6f6a3a0d7c73b93a4638890b531003091f4a7d813594916467bb6273f9e0e3ba"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb3112c2a8702c67f","typeKey":"ImageLifecycle_7dbeae","componentTag":"citry-image-lifecycle-461b25b0","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
