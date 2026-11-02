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
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f89003914b2e0ff39d3104241a410a162394559ce6b84c104b10cfb4dfafd6c4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-menu",
    popover: "manual",
    role: "menu",
    "data-citry-menu-root": "",
    "data-citry-ui-part": "menu"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall128e51e25bbf9b14.id,
      key: _ctx.$citryPrepared.calls.citryCall128e51e25bbf9b14.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallad10cfbc59f21a56.id,
      key: _ctx.$citryPrepared.calls.citryCallad10cfbc59f21a56.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["350796590b94daa634389ca370905ccec7328772f20e9efad2c0ad47ec1cd6ac"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall128e51e25bbf9b14","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[]},{"localId":"citryCallad10cfbc59f21a56","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

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
      }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
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
    }, null, 8 /* PROPS */, ["citry-id"]))
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7d272725d66788988945320eb99d30b26b555cd29b84d00af0f49a69545cba27"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall13ddc2b7f50a2d82","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_split_button_b0dde971 = _resolveComponent("citry-c-split-button-b0dde971")
  
  return (_openBlock(), _createElementBlock("section", { class: "split-button-basic" }, [
    _createElementVNode("article", null, [
      _createElementVNode("p", null, "Template composition"),
      (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall6d31905efe0b1531.id,
        key: _ctx.$citryPrepared.calls.citryCall6d31905efe0b1531.key
      }, {
        ['citrySlot7be091cc12a38e21']: _withCtx(() => [
          _createTextVNode("Save specimen")
        ]),
        ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalla371a0306193ed11.id,
            key: _ctx.$citryPrepared.calls.citryCalla371a0306193ed11.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Save a copy")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall9ed87eddbe7a5b5b.id,
            key: _ctx.$citryPrepared.calls.citryCall9ed87eddbe7a5b5b.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Export record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("p", null, "Python composition"),
      (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalla550b15765e8bb99.id,
        key: _ctx.$citryPrepared.calls.citryCalla550b15765e8bb99.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1f12965e16fdc84def1d798a1442b1e8800f5b504e6636cc48be95535f84c09c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla371a0306193ed11","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9ed87eddbe7a5b5b","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6d31905efe0b1531","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall9ed87eddbe7a5b5b","citryCalla371a0306193ed11"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla550b15765e8bb99","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_basic_split_button_actions_a9a2ee50 = _resolveComponent("citry-basic-split-button-actions-a9a2ee50")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_basic_split_button_actions_a9a2ee50, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1722b97ebf19caf3.id,
      key: _ctx.$citryPrepared.calls.citryCall1722b97ebf19caf3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4e14867ccacdffd90489d53a311bd2e7121acf5b34091d8051c7cb658771f522"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1722b97ebf19caf3","typeKey":"BasicSplitButtonActions_f4b463","componentTag":"citry-basic-split-button-actions-a9a2ee50","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
