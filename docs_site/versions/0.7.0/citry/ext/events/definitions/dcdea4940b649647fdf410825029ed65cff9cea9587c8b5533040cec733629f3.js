(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-popover-host",
    "data-citry-popover-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot371618f8b14ff656'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot371618f8b14ff656", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-popover",
      popover: "manual",
      role: "dialog",
      tabindex: "-1",
      "data-citry-ui-part": "popover"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("header", {
        class: "cui-popover__header",
        "data-citry-ui-part": "header"
      }, [
        _createElementVNode("h2", _mergeProps({
          class: "cui-popover__title",
          "data-citry-ui-part": "title"
        }, _ctx.$citryPrepared.citryAttrs1), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot6797d7221c481487'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot6797d7221c481487", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ]),
      _createElementVNode("div", {
        class: "cui-popover__body",
        "data-citry-ui-part": "body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot324bf05fa215c365'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot324bf05fa215c365", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2b649a5f47d1d9e8e1b8f057ac12e41dfe825104ddb7610df5fe7acaa7676ffe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-scroll-area",
    tabindex: "0",
    "data-citry-ui-part": "scroll-area"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotdbd1d2942e04f334'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotdbd1d2942e04f334", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1515467170c655985883a90412c7d03f74d07fe291843c485cc0e24885499234"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_popover_e1fe086e = _resolveComponent("citry-c-popover-e1fe086e")
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-overlay-boundary" }, [
    _createElementVNode("h2", null, "Credential review"),
    _createElementVNode("p", null, " The red sample is ordinary positioned content and clips at the viewport. The Popover follows its own anchored-layer contract. "),
    (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld405907fe06fd33e.id,
      key: _ctx.$citryPrepared.calls.citryCalld405907fe06fd33e.key
    }, {
      ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
        _createElementVNode("div", { class: "scroll-area-overlay-boundary__content" }, [
          _createElementVNode("span", { class: "scroll-area-overlay-boundary__clipped" }, " Ordinary positioned note "),
          _createElementVNode("p", null, "Confirm the token owner and intended service boundary."),
          _createElementVNode("p", null, "Review the current scopes before granting another permission."),
          (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallb0699761721c96ec.id,
            key: _ctx.$citryPrepared.calls.citryCallb0699761721c96ec.key
          }, {
            ['citrySlot371618f8b14ff656']: _withCtx(() => [
              (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
                "citry-id": _ctx.$citryPrepared.calls.citryCall34eeaa8862d869ad.id,
                key: _ctx.$citryPrepared.calls.citryCall34eeaa8862d869ad.key
              }, {
                ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                  _createTextVNode("Open scope help")
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ]),
            ['citrySlot6797d7221c481487']: _withCtx(() => [
              _createTextVNode("Credential scope")
            ]),
            ['citrySlot324bf05fa215c365']: _withCtx(() => [
              _createTextVNode(" Grant only the permissions this worker needs. ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          _createElementVNode("p", null, "Record the approval before rotating the credential."),
          _createElementVNode("p", null, "Archive the previous key after the overlap window closes.")
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3272ce763dea9b66e79747e8266cddc607dc27e3b560c13fbfa4e09565d30b4f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall34eeaa8862d869ad","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb0699761721c96ec","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCall34eeaa8862d869ad"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld405907fe06fd33e","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":["citryCall34eeaa8862d869ad","citryCallb0699761721c96ec"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_overlay_boundary_fc109355 = _resolveComponent("citry-scroll-area-overlay-boundary-fc109355")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_overlay_boundary_fc109355, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallc54a2bf94fbfc909.id,
      key: _ctx.$citryPrepared.calls.citryCallc54a2bf94fbfc909.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3b0a58a0524b0a3655aa0a4b99888eed3047cd83520c9df5d3d1bc333d459af0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc54a2bf94fbfc909","typeKey":"ScrollAreaOverlayBoundary_3848a4","componentTag":"citry-scroll-area-overlay-boundary-fc109355","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
