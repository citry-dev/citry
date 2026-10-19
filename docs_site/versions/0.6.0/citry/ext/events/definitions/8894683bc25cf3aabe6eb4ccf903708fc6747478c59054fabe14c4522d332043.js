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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "m21 21-4.34-4.34" }),
      _createElementVNode("circle", {
        cx: "11",
        cy: "11",
        r: "8"
      })
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e644e4372deb1060e9ceb21b420883fa87440e48866682e727eeb915c7ead2ab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", {
      class: "cui-menu__item-start",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-start"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot445c6c6a0da32c02'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot445c6c6a0da32c02", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1914d19b2433c73f'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1914d19b2433c73f", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-description",
        "data-citry-ui-part": "menu-item-description"
      }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot78539127ef118382'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot78539127ef118382", { key: 2 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("span", {
      class: "cui-menu__item-end",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-end"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotc69fa79170a59085'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotc69fa79170a59085", { key: 3 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1651f1884948a51bab1c9bdf8beb8be818f532b8a5780f6d8dde1e26804383c1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z" })
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4f7639482e91b7ad7a2108c8f1dbe7f4544e44c488830449ab9ccc26f72f8024"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", {
      class: "cui-menu__item-start",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-start"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot445c6c6a0da32c02'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot445c6c6a0da32c02", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1914d19b2433c73f'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1914d19b2433c73f", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("span", {
      class: "cui-menu__item-end",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-end"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotc69fa79170a59085'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotc69fa79170a59085", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2ecb6f5ec4c0f17e9c4abd423cb03ac7697dbcb3df75ae505e5cfb41f1bbe7d6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2dd141883a0b86e46f4dee372ca395da9eba7d6cbe04575f124612c3a26de1af"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, renderSlot: _renderSlot, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_internal_menu_surface_37f82339 = _resolveComponent("citry-c-internal-menu-surface-37f82339")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-menu-host",
    "data-citry-menu-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlote9035851c53b236c'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlote9035851c53b236c", { key: 0 })
      : _createCommentVNode("v-if", true),
    (_openBlock(), _createBlock(_component_citry_c_internal_menu_surface_37f82339, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9ee6b0021ed574b1.id,
      key: _ctx.$citryPrepared.calls.citryCall9ee6b0021ed574b1.key
    }, {
      ['citrySlot5176cbf97df342fc']: _withCtx(() => [
        _renderSlot(_ctx.$slots, "citrySlot4a45b3d88f07d9ae")
      ]),
      _: 3 /* FORWARDED */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5caaa212e918fd84255d00678dcb422a9d67fa38e055cc4224bd041a3897028e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9ee6b0021ed574b1","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlot4a45b3d88f07d9ae"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_icon_f8b347d7 = _resolveComponent("citry-c-icon-f8b347d7")
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_menu_0bdb31ef = _resolveComponent("citry-c-menu-0bdb31ef")
  
  return (_openBlock(), _createElementBlock("section", { class: "archive-content-demo" }, [
    (_openBlock(), _createBlock(_component_citry_c_menu_0bdb31ef, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall078813bef8a35d62.id,
      key: _ctx.$citryPrepared.calls.citryCall078813bef8a35d62.key
    }, {
      ['citrySlote9035851c53b236c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall4020478e25a4b7d6.id,
          key: _ctx.$citryPrepared.calls.citryCall4020478e25a4b7d6.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Catalog tools")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot4a45b3d88f07d9ae']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall3bdf3b441382d690.id,
          key: _ctx.$citryPrepared.calls.citryCall3bdf3b441382d690.key
        }, {
          ['citrySlot445c6c6a0da32c02']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall93f02016a7cedd6d.id,
              key: _ctx.$citryPrepared.calls.citryCall93f02016a7cedd6d.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          ['citrySlot1914d19b2433c73f']: _withCtx(() => [
            _createTextVNode("Search illuminated texts")
          ]),
          ['citrySlot78539127ef118382']: _withCtx(() => [
            _createTextVNode("Find titles, scribes, and sigils.")
          ]),
          ['citrySlotc69fa79170a59085']: _withCtx(() => [
            _createElementVNode("kbd", null, "⌘ K")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall926db7f985e5a967.id,
          key: _ctx.$citryPrepared.calls.citryCall926db7f985e5a967.key
        }, {
          ['citrySlot445c6c6a0da32c02']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallfa7d445f1ce4b1b1.id,
              key: _ctx.$citryPrepared.calls.citryCallfa7d445f1ce4b1b1.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          ['citrySlot1914d19b2433c73f']: _withCtx(() => [
            _createTextVNode("Mark this passage")
          ]),
          ['citrySlotc69fa79170a59085']: _withCtx(() => [
            _createElementVNode("kbd", null, "M")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ce9e08a8da8e8bef8d1ab2ecdf05baf354abdddd1fe08b93016f810b2bf3d752"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4020478e25a4b7d6","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall93f02016a7cedd6d","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCall3bdf3b441382d690","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlot1914d19b2433c73f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot445c6c6a0da32c02","localDescendants":["citryCall93f02016a7cedd6d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot78539127ef118382","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc69fa79170a59085","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallfa7d445f1ce4b1b1","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCall926db7f985e5a967","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlot1914d19b2433c73f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot445c6c6a0da32c02","localDescendants":["citryCallfa7d445f1ce4b1b1"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc69fa79170a59085","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall078813bef8a35d62","typeKey":"CMenu_4350e4","componentTag":"citry-c-menu-0bdb31ef","bindings":[],"fills":[{"name":"citrySlot4a45b3d88f07d9ae","localDescendants":["citryCall3bdf3b441382d690","citryCall926db7f985e5a967","citryCall93f02016a7cedd6d","citryCallfa7d445f1ce4b1b1"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote9035851c53b236c","localDescendants":["citryCall4020478e25a4b7d6"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_menu_item_content_db90878c = _resolveComponent("citry-menu-item-content-db90878c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_menu_item_content_db90878c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall42b5bfb32e263193.id,
      key: _ctx.$citryPrepared.calls.citryCall42b5bfb32e263193.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["15f00cd6281e5b69e8d980157c03c21c05448d8dcdb2f9b6cab6e3fce051ac9f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall42b5bfb32e263193","typeKey":"MenuItemContent_53a1eb","componentTag":"citry-menu-item-content-db90878c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
