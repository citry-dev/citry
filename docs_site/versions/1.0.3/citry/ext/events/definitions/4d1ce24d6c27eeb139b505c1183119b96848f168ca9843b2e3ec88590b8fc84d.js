(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlotf1817a57bc1354a1'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotf1817a57bc1354a1", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d90350988f10d21b47c3fe72e3948c038edba9d3a6978d531b6920a500081185"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-menu",
    popover: "manual",
    role: "menu",
    "data-citry-menu-root": "",
    "data-citry-ui-part": "menu"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot5176cbf97df342fc'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot5176cbf97df342fc", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5724fe4436c7b03d9f8295b958e822aaa5b29cb5e0b2c2a376f508224206ef60"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_internal_menu_surface_37f82339 = _resolveComponent("citry-c-internal-menu-surface-37f82339")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-split-button",
    role: "group",
    "data-citry-menu-host": "",
    "data-citry-ui-part": "split-button"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("button", _mergeProps({
      class: "cui-button cui-split-button__primary",
      "data-citry-ui-part": "split-button-primary"
    }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("span", _mergeProps({
        class: "cui-button__loading",
        "aria-hidden": "true",
        "data-citry-ui-part": "split-button-primary-loading-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot8e6c3d3fdbd8f918'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot8e6c3d3fdbd8f918", { key: 0 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot8e6c3d3fdbd8f918'] === 'fallback')
            ? (_openBlock(), _createElementBlock("span", {
              key: 1,
              class: "cui-button__spinner"
            }))
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", {
        class: "cui-button__content",
        "data-citry-ui-part": "split-button-primary-content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot7be091cc12a38e21'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot7be091cc12a38e21", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("button", _mergeProps({
      class: "cui-button cui-split-button__menu-trigger",
      type: "button",
      "aria-haspopup": "menu",
      "data-citry-menu-trigger": "",
      "data-citry-ui-part": "split-button-menu-trigger"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("span", {
        class: "cui-split-button__indicator",
        "aria-hidden": "true",
        "data-citry-ui-part": "split-button-menu-indicator"
      })
    ], 16 /* FULL_PROPS */),
    (_openBlock(), _createBlock(_component_citry_c_internal_menu_surface_37f82339, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall13ddc2b7f50a2d82.id,
      key: _ctx.$citryPrepared.calls.citryCall13ddc2b7f50a2d82.key
    }, {
      ['citrySlot5176cbf97df342fc']: _withCtx(() => [
        _renderSlot(_ctx.$slots, "citrySlotd19ad2b891ac8270")
      ]),
      _: 3 /* FORWARDED */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9da8a1bac85efc6320e657a9ef0fb0ed0f340817d8d7f3b39148669f1ea03ec4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall13ddc2b7f50a2d82","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlotd19ad2b891ac8270"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_split_button_b0dde971 = _resolveComponent("citry-c-split-button-b0dde971")
  
  return (_openBlock(), _createElementBlock("section", { class: "split-button-glance" }, [
    _createElementVNode("p", { class: "split-button-glance__eyebrow" }, "Field journal"),
    _createElementVNode("h2", null, "Alpine gentian specimen"),
    _createElementVNode("p", null, "Keep the primary save action visible and related work nearby."),
    (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, _mergeProps({ ref: "split" }, {onAction:(value)=>_ctx.last=value}, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall44ca856ac155615b.id,
      key: _ctx.$citryPrepared.calls.citryCall44ca856ac155615b.key
    }), {
      ['citrySlot7be091cc12a38e21']: _withCtx(() => [
        _createTextVNode(" Save specimen ")
      ]),
      ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld945c7da077407bf.id,
          key: _ctx.$citryPrepared.calls.citryCalld945c7da077407bf.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Save a copy")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallc8c86378ddbde578.id,
          key: _ctx.$citryPrepared.calls.citryCallc8c86378ddbde578.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Export record")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall58496b5eb7e1aaa8.id,
          key: _ctx.$citryPrepared.calls.citryCall58496b5eb7e1aaa8.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode(" Archive specimen ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.last)
    }, "No action yet", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["022c7dfde5241af52400410031899bf79d36305bb6a2581f3207391b19e771aa"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld945c7da077407bf","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc8c86378ddbde578","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall58496b5eb7e1aaa8","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall44ca856ac155615b","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[{"kind":"ref-static","name":"ref","value":"split","sourceStart":238,"sourceEnd":249},{"kind":"props-object","name":"v-bind","value":"{onAction:(value)=>last=value}","sourceStart":250,"sourceEnd":289}],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall58496b5eb7e1aaa8","citryCallc8c86378ddbde578","citryCalld945c7da077407bf"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_split_button_at_a_glance_3c31f471 = _resolveComponent("citry-split-button-at-a-glance-3c31f471")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_split_button_at_a_glance_3c31f471, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall35e9ed8ab8d59809.id,
      key: _ctx.$citryPrepared.calls.citryCall35e9ed8ab8d59809.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["65cb346621917925f2b2d8068c92537945abffe0de41c4247d1379a439c15d31"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall35e9ed8ab8d59809","typeKey":"SplitButtonAtAGlance_1d6608","componentTag":"citry-split-button-at-a-glance-3c31f471","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
